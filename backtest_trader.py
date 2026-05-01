#!/usr/bin/env python3
"""Backtest dla strategii SMA+RSI+MACD z crypto_auto_trader.py."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import ccxt
from crypto_auto_trader import (
    TraderConfig,
    decide_signal,
    load_config as _load_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backtest dla strategii SMA+RSI+MACD"
    )
    parser.add_argument(
        "--config", default="trader_config.json", help="Sciezka do konfiguracji JSON"
    )
    parser.add_argument(
        "--limit", type=int, default=1000, help="Liczba swiec do pobrania"
    )
    return parser.parse_args()


def load_config(path: Path) -> TraderConfig:
    return _load_config(path)


def main() -> int:
    args = parse_args()
    cfg = load_config(Path(args.config))

    exchange_cls = getattr(ccxt, cfg.exchange)
    ex = exchange_cls({"enableRateLimit": True})
    ex.load_markets()

    limit = max(args.limit, cfg.slow_sma + cfg.macd_slow + cfg.macd_signal + 10)
    candles = ex.fetch_ohlcv(cfg.symbol, cfg.timeframe, limit=limit)
    closes = [float(c[4]) for c in candles]

    position_open = False
    entry_price = 0.0
    amount = 0.0
    pnl_quote = 0.0
    trades = 0
    wins = 0
    stop_losses = 0
    take_profits = 0

    # Minimalne okno: slow_sma + macd_slow + macd_signal
    min_window = cfg.slow_sma + cfg.macd_slow + cfg.macd_signal + 5
    for i in range(min_window, len(closes)):
        window = closes[: i + 1]
        price = window[-1]

        try:
            signal = decide_signal(window, cfg)
        except ValueError:
            continue

        if position_open:
            stop_loss_price = entry_price * (1.0 - cfg.stop_loss_pct)
            take_profit_price = entry_price * (1.0 + cfg.take_profit_pct)
            if price <= stop_loss_price:
                risk_exit = "stop_loss"
            elif price >= take_profit_price:
                risk_exit = "take_profit"
            else:
                risk_exit = None
        else:
            risk_exit = None

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
            if risk_exit == "stop_loss":
                stop_losses += 1
            elif risk_exit == "take_profit":
                take_profits += 1
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
    print("BACKTEST SUMMARY — strategia SMA+RSI+MACD")
    print("=" * 70)
    print(f"Exchange:             {cfg.exchange}")
    print(f"Symbol:               {cfg.symbol}")
    print(f"Timeframe:            {cfg.timeframe}")
    print(f"Candles:              {len(closes)}")
    print(f"Strategia:            SMA({cfg.fast_sma}/{cfg.slow_sma}) + RSI(14) + MACD({cfg.macd_fast},{cfg.macd_slow},{cfg.macd_signal})")
    print(f"Transakcje:           {trades}")
    print(f"Win rate:             {win_rate:.2f}%")
    print(f"Stop-lossy:           {stop_losses}")
    print(f"Take-profity:         {take_profits}")
    print(f"PnL (quote):          {pnl_quote:+.4f}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
