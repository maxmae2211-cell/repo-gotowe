#!/usr/bin/env python3
"""Prosty auto trader krypto z domyslnym trybem paper.

Strategia:
- Przeciecie SMA szybkiej i wolnej do wejsc/wyjsc.
- Ochrona pozycji przez stop loss i take profit.

Domyslnie dziala paper trading. Tryb live wymaga flagi --live i kluczy API.
"""

from __future__ import annotations
from typing import List, Any, TypedDict

import argparse
import csv
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import ccxt


@dataclass
class TraderConfig:
    exchange: str
    symbol: str
    timeframe: str
    fast_sma: int
    slow_sma: int
    quote_allocation: float
    stop_loss_pct: float
    take_profit_pct: float
    poll_seconds: int
    state_file: str
    trade_log_file: str
    db_file: str = "trader_trades.db"
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto trader krypto")
    parser.add_argument(
        "--config",
        default="trader_config.json",
        help="Sciezka do pliku konfiguracji JSON",
    )
    parser.add_argument(
        "--live", action="store_true", help="Wlacz live trading (realne zlecenia)"
    )
    parser.add_argument(
        "--once", action="store_true", help="Wykonaj jeden cykl i zakoncz"
    )
    return parser.parse_args()


def load_config(path: Path) -> TraderConfig:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return TraderConfig(**data)


def load_state(path: Path) -> dict[str, Any]:
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return {
        "position_open": False,
        "entry_price": 0.0,
        "amount": 0.0,
        "last_signal": "none",
        "updated_at": 0,
    }


def save_state(path: Path, state: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def append_trade_log(path: Path, event: dict[str, Any]) -> None:
    file_exists = path.exists()
    fieldnames = [
        "timestamp_utc",
        "symbol",
        "mode",
        "action",
        "reason",
        "price",
        "amount",
        "quote_value",
    ]
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(event)


class TraderState(TypedDict, total=False):
    entry_price: float
    # Dodaj inne pola stanu, jeśli są używane


def sma(values: List[float], length: int) -> float:
    if len(values) < length:
        raise ValueError(f"Za malo swiec dla SMA{length}")
    return sum(values[-length:]) / length


def rsi(values: List[float], period: int = 14) -> float:
    """Oblicza RSI (Relative Strength Index) dla ostatnich `period` zmian."""
    if len(values) < period + 1:
        raise ValueError(f"Za malo swiec dla RSI{period}")
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [d if d > 0 else 0.0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0.0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def ema(values: List[float], period: int) -> List[float]:
    """Oblicza EMA (Exponential Moving Average) dla całej serii."""
    if len(values) < period:
        raise ValueError(f"Za malo danych dla EMA{period}")
    k = 2.0 / (period + 1)
    result = [sum(values[:period]) / period]
    for v in values[period:]:
        result.append(v * k + result[-1] * (1 - k))
    return result


def macd(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """Zwraca (macd_line, signal_line, histogram) dla ostatniego punktu."""
    if len(values) < slow + signal:
        raise ValueError(f"Za malo danych dla MACD({fast},{slow},{signal})")
    ema_fast = ema(values, fast)
    ema_slow = ema(values, slow)
    # Wyrównaj długości
    diff = len(ema_fast) - len(ema_slow)
    ema_fast = ema_fast[diff:]
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    if len(macd_line) < signal:
        raise ValueError("Za malo danych dla linii sygnalu MACD")
    signal_line = ema(macd_line, signal)
    histogram = macd_line[-1] - signal_line[-1]
    return macd_line[-1], signal_line[-1], histogram


def init_db(path: Path) -> None:
    """Inicjalizuje bazę SQLite z tabelą transakcji."""
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            symbol TEXT NOT NULL,
            mode TEXT NOT NULL,
            action TEXT NOT NULL,
            reason TEXT NOT NULL,
            price REAL NOT NULL,
            amount REAL NOT NULL,
            quote_value REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def append_trade_db(path: Path, event: dict[str, Any]) -> None:
    """Zapisuje transakcję do bazy SQLite."""
    conn = sqlite3.connect(path)
    conn.execute("""
        INSERT INTO trades
            (timestamp_utc, symbol, mode, action, reason, price, amount, quote_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event["timestamp_utc"], event["symbol"], event["mode"], event["action"],
        event["reason"], float(event["price"]), float(event["amount"]),
        float(event["quote_value"]),
    ))
    conn.commit()
    conn.close()


def build_exchange(cfg: 'TraderConfig', live: bool) -> Any:
    exchange_cls = getattr(ccxt, cfg.exchange)
    params: dict[str, Any] = {"enableRateLimit": True}

    if live:
        key = os.getenv("EXCHANGE_API_KEY", "")
        secret = os.getenv("EXCHANGE_API_SECRET", "")
        if not key or not secret:
            raise RuntimeError("Brak EXCHANGE_API_KEY / EXCHANGE_API_SECRET")
        params["apiKey"] = key
        params["secret"] = secret

    ex = exchange_cls(params)
    ex.load_markets()
    if cfg.symbol not in ex.markets:
        raise RuntimeError(f"Symbol niedostepny na gieldzie: {cfg.symbol}")
    return ex


def decide_signal(closes: list[float], cfg: TraderConfig) -> str:
    fast_sma_values = [sum(closes[i-cfg.fast_sma:i]) /
                       cfg.fast_sma for i in range(cfg.fast_sma, len(closes)+1)]
    slow_sma_values = [sum(closes[i-cfg.slow_sma:i]) /
                       cfg.slow_sma for i in range(cfg.slow_sma, len(closes)+1)]

    fast_now = fast_sma_values[-1]
    slow_now = slow_sma_values[-1]
    fast_prev = fast_sma_values[-2] if len(fast_sma_values) > 1 else fast_now
    slow_prev = slow_sma_values[-2] if len(slow_sma_values) > 1 else slow_now

    crossed_up = fast_prev <= slow_prev and fast_now > slow_now
    crossed_down = fast_prev >= slow_prev and fast_now < slow_now

    try:
        rsi_value = rsi(closes, period=14)
    except ValueError:
        rsi_value = 50.0

    try:
        macd_line, signal_line, _ = macd(
            closes, fast=cfg.macd_fast, slow=cfg.macd_slow, signal=cfg.macd_signal
        )
        macd_bullish = macd_line > signal_line
        macd_bearish = macd_line < signal_line
    except ValueError:
        macd_bullish = True
        macd_bearish = True

    if crossed_up and rsi_value < 70 and macd_bullish:
        return "buy"
    if crossed_down and rsi_value > 30 and macd_bearish:
        return "sell"
    return "hold"


def maybe_risk_exit(last_price: float, state: dict[str, Any], cfg: TraderConfig) -> str:
    if not state["position_open"]:
        return "none"

    entry = float(state["entry_price"])
    stop_loss_price = entry * (1.0 - cfg.stop_loss_pct)
    take_profit_price = entry * (1.0 + cfg.take_profit_pct)

    if last_price <= stop_loss_price:
        return "stop_loss"
    if last_price >= take_profit_price:
        return "take_profit"
    return "none"


def place_buy(exchange, cfg: TraderConfig, last_price: float, live: bool) -> float:
    amount = cfg.quote_allocation / last_price
    if live:
        exchange.create_market_buy_order(cfg.symbol, amount)
    return amount


def place_sell(exchange, cfg: TraderConfig, amount: float, live: bool) -> None:
    if live and amount > 0:
        exchange.create_market_sell_order(cfg.symbol, amount)


def run_cycle(
    exchange, cfg: TraderConfig, state: dict[str, Any], live: bool
) -> dict[str, Any]:
    candles = exchange.fetch_ohlcv(
        cfg.symbol, cfg.timeframe, limit=max(cfg.slow_sma + 5, 60)
    )
    closes = [float(c[4]) for c in candles]
    if len(closes) < cfg.slow_sma + 2:
        raise RuntimeError("Za malo swiec do oceny strategii")

    last_price = closes[-1]
    signal = decide_signal(closes, cfg)
    risk_signal = maybe_risk_exit(last_price, state, cfg)

    try:
        rsi_val = rsi(closes, period=14)
    except ValueError:
        rsi_val = float("nan")

    try:
        macd_val, macd_sig, macd_hist = macd(
            closes, fast=cfg.macd_fast, slow=cfg.macd_slow, signal=cfg.macd_signal
        )
    except ValueError:
        macd_val = macd_sig = macd_hist = float("nan")

    print(
        f"cena={last_price:.4f} rsi={rsi_val:.1f} macd={macd_val:.2f}/{macd_sig:.2f} "
        f"sygnal={signal} ryzyko={risk_signal} pozycja_otwarta={state['position_open']}"
    )

    if not state["position_open"] and signal == "buy":
        amount = place_buy(exchange, cfg, last_price, live)
        state["position_open"] = True
        state["entry_price"] = last_price
        state["amount"] = amount
        state["last_signal"] = "buy"
        print(
            f"KUPNO ilosc={amount:.8f} po_cenie={last_price:.4f} tryb={'live' if live else 'paper'}"
        )
        trade_event = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "symbol": cfg.symbol,
            "mode": "live" if live else "paper",
            "action": "buy",
            "reason": "sma_cross_up",
            "price": f"{last_price:.8f}",
            "amount": f"{amount:.8f}",
            "quote_value": f"{cfg.quote_allocation:.8f}",
        }
        append_trade_log(Path(cfg.trade_log_file), trade_event)
        append_trade_db(Path(cfg.db_file), trade_event)

    elif state["position_open"] and (
        signal == "sell" or risk_signal in {"stop_loss", "take_profit"}
    ):
        place_sell(exchange, cfg, float(state["amount"]), live)
        print(
            f"SPRZEDAZ ilosc={float(state['amount']):.8f} po_cenie={last_price:.4f} powod="
            f"{risk_signal if risk_signal != 'none' else signal} tryb={'live' if live else 'paper'}"
        )
        reason = risk_signal if risk_signal != "none" else signal
        trade_event = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "symbol": cfg.symbol,
            "mode": "live" if live else "paper",
            "action": "sell",
            "reason": reason,
            "price": f"{last_price:.8f}",
            "amount": f"{float(state['amount']):.8f}",
            "quote_value": f"{float(state['amount']) * last_price:.8f}",
        }
        append_trade_log(Path(cfg.trade_log_file), trade_event)
        append_trade_db(Path(cfg.db_file), trade_event)
        state["position_open"] = False
        state["entry_price"] = 0.0
        state["amount"] = 0.0
        state["last_signal"] = "sell"

    state["updated_at"] = int(time.time())
    return state


def main() -> int:
    args = parse_args()
    cfg = load_config(Path(args.config))
    state_path = Path(cfg.state_file)
    state = load_state(state_path)

    print(
        f"Start tradera tryb={'LIVE' if args.live else 'PAPER'} symbol={cfg.symbol}")
    init_db(Path(cfg.db_file))
    exchange = build_exchange(cfg, args.live)

    while True:
        try:
            state = run_cycle(exchange, cfg, state, args.live)
            save_state(state_path, state)
        except Exception as exc:
            print(f"BLAD: {exc}")

        if args.once:
            break
        time.sleep(cfg.poll_seconds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
