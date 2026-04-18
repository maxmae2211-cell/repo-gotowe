#!/usr/bin/env python3
"""Simple crypto auto trader with paper mode by default.

Strategy:
- SMA fast/slow crossover for entries/exits.
- Stop loss and take profit protections.

Default mode is paper trading. Live mode requires --live and API env vars.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crypto auto trader")
    parser.add_argument("--config", default="trader_config.json", help="Path to config JSON")
    parser.add_argument("--live", action="store_true", help="Enable live trading (real orders)")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
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


def sma(values: list[float], length: int) -> float:
    if len(values) < length:
        raise ValueError(f"Not enough candles for SMA{length}")
    return sum(values[-length:]) / length


def build_exchange(cfg: TraderConfig, live: bool):
    exchange_cls = getattr(ccxt, cfg.exchange)
    params: dict[str, Any] = {"enableRateLimit": True}

    if live:
        key = os.getenv("EXCHANGE_API_KEY", "")
        secret = os.getenv("EXCHANGE_API_SECRET", "")
        if not key or not secret:
            raise RuntimeError("Missing EXCHANGE_API_KEY / EXCHANGE_API_SECRET")
        params["apiKey"] = key
        params["secret"] = secret

    ex = exchange_cls(params)
    ex.load_markets()
    if cfg.symbol not in ex.markets:
        raise RuntimeError(f"Symbol not available on exchange: {cfg.symbol}")
    return ex


def decide_signal(closes: list[float], cfg: TraderConfig) -> str:
    fast_now = sma(closes, cfg.fast_sma)
    slow_now = sma(closes, cfg.slow_sma)

    fast_prev = sma(closes[:-1], cfg.fast_sma)
    slow_prev = sma(closes[:-1], cfg.slow_sma)

    crossed_up = fast_prev <= slow_prev and fast_now > slow_now
    crossed_down = fast_prev >= slow_prev and fast_now < slow_now

    if crossed_up:
        return "buy"
    if crossed_down:
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


def run_cycle(exchange, cfg: TraderConfig, state: dict[str, Any], live: bool) -> dict[str, Any]:
    candles = exchange.fetch_ohlcv(cfg.symbol, cfg.timeframe, limit=max(cfg.slow_sma + 5, 60))
    closes = [float(c[4]) for c in candles]
    if len(closes) < cfg.slow_sma + 2:
        raise RuntimeError("Not enough candles to evaluate strategy")

    last_price = closes[-1]
    signal = decide_signal(closes, cfg)
    risk_signal = maybe_risk_exit(last_price, state, cfg)

    print(f"price={last_price:.4f} signal={signal} risk={risk_signal} open={state['position_open']}")

    if not state["position_open"] and signal == "buy":
        amount = place_buy(exchange, cfg, last_price, live)
        state["position_open"] = True
        state["entry_price"] = last_price
        state["amount"] = amount
        state["last_signal"] = "buy"
        print(f"BUY amount={amount:.8f} at={last_price:.4f} mode={'live' if live else 'paper'}")

    elif state["position_open"] and (signal == "sell" or risk_signal in {"stop_loss", "take_profit"}):
        place_sell(exchange, cfg, float(state["amount"]), live)
        print(
            f"SELL amount={float(state['amount']):.8f} at={last_price:.4f} reason="
            f"{risk_signal if risk_signal != 'none' else signal} mode={'live' if live else 'paper'}"
        )
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

    print(f"Starting trader mode={'LIVE' if args.live else 'PAPER'} symbol={cfg.symbol}")
    exchange = build_exchange(cfg, args.live)

    while True:
        try:
            state = run_cycle(exchange, cfg, state, args.live)
            save_state(state_path, state)
        except Exception as exc:
            print(f"ERROR: {exc}")

        if args.once:
            break
        time.sleep(cfg.poll_seconds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
