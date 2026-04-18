#!/usr/bin/env python3
"""Simple backtest runner for the SMA crossover strategy used by crypto_auto_trader.py."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

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


def sma(values: list[float], length: int) -> float:
    if len(values) < length:
        raise ValueError(f"Not enough candles for SMA{length}")
    return sum(values[-length:]) / length


def decide_signal(closes: list[float], cfg: TraderConfig) -> str:
    fast_now = sma(closes, cfg.fast_sma)
    slow_now = sma(closes, cfg.slow_sma)
    fast_prev = sma(closes[:-1], cfg.fast_sma)
    slow_prev = sma(closes[:-1], cfg.slow_sma)

    if fast_prev <= slow_prev and fast_now > slow_now:
        return "buy"
    if fast_prev >= slow_prev and fast_now < slow_now:
        return "sell"
    return "hold"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest for crypto_auto_trader strategy")
    parser.add_argument("--config", default="trader_config.json", help="Path to config JSON")
    parser.add_argument("--limit", type=int, default=1000, help="Number of candles to fetch")
    return parser.parse_args()


def load_config(path: Path) -> TraderConfig:
    with path.open("r", encoding="utf-8") as handle:
        return TraderConfig(**json.load(handle))


def main() -> int:
    args = parse_args()
    cfg = load_config(Path(args.config))

    exchange_cls = getattr(ccxt, cfg.exchange)
    ex = exchange_cls({"enableRateLimit": True})
    ex.load_markets()

    candles = ex.fetch_ohlcv(cfg.symbol, cfg.timeframe, limit=max(args.limit, cfg.slow_sma + 10))
    closes = [float(c[4]) for c in candles]
    times = [int(c[0]) for c in candles]

    position_open = False
    entry_price = 0.0
    amount = 0.0
    pnl_quote = 0.0
    trades = 0
    wins = 0

    start = cfg.slow_sma + 2
    for i in range(start, len(closes)):
        window = closes[: i + 1]
        price = window[-1]

        signal = decide_signal(window, cfg)

        if position_open:
            stop_loss_price = entry_price * (1.0 - cfg.stop_loss_pct)
            take_profit_price = entry_price * (1.0 + cfg.take_profit_pct)
            risk_exit = price <= stop_loss_price or price >= take_profit_price
        else:
            risk_exit = False

        if not position_open and signal == "buy":
            amount = cfg.quote_allocation / price
            entry_price = price
            position_open = True
            continue

        if position_open and (signal == "sell" or risk_exit):
            trade_pnl = amount * (price - entry_price)
            pnl_quote += trade_pnl
            trades += 1
            if trade_pnl > 0:
                wins += 1
            position_open = False
            entry_price = 0.0
            amount = 0.0

    if position_open:
        final_price = closes[-1]
        trade_pnl = amount * (final_price - entry_price)
        pnl_quote += trade_pnl
        trades += 1
        if trade_pnl > 0:
            wins += 1

    win_rate = (wins / trades * 100.0) if trades else 0.0

    print("=" * 70)
    print("BACKTEST SUMMARY")
    print("=" * 70)
    print(f"Exchange:             {cfg.exchange}")
    print(f"Symbol:               {cfg.symbol}")
    print(f"Timeframe:            {cfg.timeframe}")
    print(f"Candles:              {len(closes)}")
    print(f"Trades:               {trades}")
    print(f"Win rate:             {win_rate:.2f}%")
    print(f"PnL (quote asset):    {pnl_quote:.4f}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
