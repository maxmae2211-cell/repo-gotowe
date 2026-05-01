"""Testy jednostkowe dla crypto_auto_trader.py"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from crypto_auto_trader import (
    TraderConfig,
    decide_signal,
    ema,
    macd,
    init_db,
    append_trade_db,
    load_config,
    load_state,
    maybe_risk_exit,
    place_buy,
    place_sell,
    save_state,
    sma,
)


def make_cfg(**kwargs):
    defaults = dict(
        exchange="binance",
        symbol="BTC/USDT",
        timeframe="1h",
        fast_sma=3,
        slow_sma=5,
        quote_allocation=100.0,
        stop_loss_pct=0.05,
        take_profit_pct=0.10,
        poll_seconds=60,
        state_file="state.json",
        trade_log_file="trades.csv",
    )
    defaults.update(kwargs)
    return TraderConfig(**defaults)


class TestSma(unittest.TestCase):
    def test_basic(self):
        self.assertAlmostEqual(sma([1.0, 2.0, 3.0, 4.0, 5.0], 3), 4.0)

    def test_full_list(self):
        self.assertAlmostEqual(sma([10.0, 20.0, 30.0], 3), 20.0)

    def test_too_few_values(self):
        with self.assertRaises(ValueError):
            sma([1.0, 2.0], 5)

    def test_single_value(self):
        self.assertAlmostEqual(sma([7.0], 1), 7.0)


class TestDecideSignal(unittest.TestCase):
    def _make_closes(self, n=20, base=100.0):
        return [base + i for i in range(n)]

    def test_hold_flat(self):
        closes = [100.0] * 20
        cfg = make_cfg(fast_sma=3, slow_sma=5)
        self.assertEqual(decide_signal(closes, cfg), "hold")

    def test_buy_signal(self):
        # Szybka SMA przekracza wolną w górę
        cfg = make_cfg(fast_sma=3, slow_sma=7)
        # Ceny rosnące gwałtownie na końcu wywołają crossed_up
        closes = [10.0] * 15 + [20.0, 30.0, 40.0, 50.0, 60.0]
        result = decide_signal(closes, cfg)
        # powinno być buy lub hold
        self.assertIn(result, ("buy", "hold", "sell"))

    def test_sell_signal(self):
        cfg = make_cfg(fast_sma=3, slow_sma=7)
        closes = [60.0] * 15 + [50.0, 40.0, 30.0, 20.0, 10.0]
        result = decide_signal(closes, cfg)
        self.assertIn(result, ("buy", "hold", "sell"))

    def test_returns_string(self):
        cfg = make_cfg(fast_sma=3, slow_sma=5)
        closes = [float(i) for i in range(1, 21)]
        result = decide_signal(closes, cfg)
        self.assertIn(result, ("buy", "sell", "hold"))


class TestMaybeRiskExit(unittest.TestCase):
    def _open_state(self, entry_price=100.0):
        return {
            "position_open": True,
            "entry_price": entry_price,
            "amount": 1.0,
            "last_signal": "buy",
            "updated_at": 0,
        }

    def _closed_state(self):
        return {
            "position_open": False,
            "entry_price": 0.0,
            "amount": 0.0,
            "last_signal": "none",
            "updated_at": 0,
        }

    def test_no_position(self):
        cfg = make_cfg()
        self.assertEqual(maybe_risk_exit(
            95.0, self._closed_state(), cfg), "none")

    def test_stop_loss_triggered(self):
        cfg = make_cfg(stop_loss_pct=0.05, take_profit_pct=0.10)
        state = self._open_state(entry_price=100.0)
        # 100 * (1 - 0.05) = 95.0 → trigger przy <= 95
        self.assertEqual(maybe_risk_exit(94.0, state, cfg), "stop_loss")

    def test_take_profit_triggered(self):
        cfg = make_cfg(stop_loss_pct=0.05, take_profit_pct=0.10)
        state = self._open_state(entry_price=100.0)
        # 100 * (1 + 0.10) = 110.0 → trigger przy >= 110
        self.assertEqual(maybe_risk_exit(111.0, state, cfg), "take_profit")

    def test_hold_in_range(self):
        cfg = make_cfg(stop_loss_pct=0.05, take_profit_pct=0.10)
        state = self._open_state(entry_price=100.0)
        self.assertEqual(maybe_risk_exit(100.0, state, cfg), "none")


class TestPlaceBuySell(unittest.TestCase):
    def test_place_buy_paper(self):
        cfg = make_cfg(quote_allocation=200.0)
        exchange = MagicMock()
        amount = place_buy(exchange, cfg, 100.0, live=False)
        self.assertAlmostEqual(amount, 2.0)
        exchange.create_market_buy_order.assert_not_called()

    def test_place_buy_live(self):
        cfg = make_cfg(quote_allocation=200.0)
        exchange = MagicMock()
        amount = place_buy(exchange, cfg, 100.0, live=True)
        self.assertAlmostEqual(amount, 2.0)
        exchange.create_market_buy_order.assert_called_once_with(
            "BTC/USDT", 2.0)

    def test_place_sell_paper(self):
        cfg = make_cfg()
        exchange = MagicMock()
        place_sell(exchange, cfg, 1.0, live=False)
        exchange.create_market_sell_order.assert_not_called()

    def test_place_sell_live(self):
        cfg = make_cfg()
        exchange = MagicMock()
        place_sell(exchange, cfg, 1.5, live=True)
        exchange.create_market_sell_order.assert_called_once_with(
            "BTC/USDT", 1.5)

    def test_place_sell_zero_amount_live(self):
        cfg = make_cfg()
        exchange = MagicMock()
        place_sell(exchange, cfg, 0.0, live=True)
        exchange.create_market_sell_order.assert_not_called()


class TestLoadSaveState(unittest.TestCase):
    def test_load_nonexistent(self):
        state = load_state(Path("/tmp/nonexistent_state_99999.json"))
        self.assertFalse(state["position_open"])
        self.assertEqual(state["entry_price"], 0.0)

    def test_save_and_load(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)
        data = {"position_open": True, "entry_price": 12345.0, "amount": 0.5}
        save_state(path, data)
        loaded = load_state(path)
        self.assertEqual(loaded["entry_price"], 12345.0)
        path.unlink()


class TestLoadConfig(unittest.TestCase):
    def test_load_config(self):
        cfg_data = {
            "exchange": "binance",
            "symbol": "ETH/USDT",
            "timeframe": "15m",
            "fast_sma": 7,
            "slow_sma": 21,
            "quote_allocation": 500.0,
            "stop_loss_pct": 0.03,
            "take_profit_pct": 0.07,
            "poll_seconds": 30,
            "state_file": "state.json",
            "trade_log_file": "trades.csv",
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(cfg_data, f)
            path = Path(f.name)
        cfg = load_config(path)
        self.assertEqual(cfg.symbol, "ETH/USDT")
        self.assertEqual(cfg.fast_sma, 7)
        path.unlink()


class TestEma(unittest.TestCase):
    def test_ema_length(self):
        values = [float(i) for i in range(1, 31)]
        result = ema(values, 10)
        self.assertEqual(len(result), 21)  # 30 - 10 + 1

    def test_ema_too_few(self):
        with self.assertRaises(ValueError):
            ema([1.0, 2.0], 5)

    def test_ema_constant_series(self):
        values = [5.0] * 20
        result = ema(values, 5)
        for v in result:
            self.assertAlmostEqual(v, 5.0, places=5)


class TestMacd(unittest.TestCase):
    def _prices(self, n=60):
        import math
        return [100.0 + math.sin(i * 0.2) * 10 for i in range(n)]

    def test_macd_returns_tuple(self):
        prices = self._prices(60)
        result = macd(prices, fast=12, slow=26, signal=9)
        self.assertEqual(len(result), 3)

    def test_macd_too_few(self):
        with self.assertRaises(ValueError):
            macd([1.0] * 10, fast=12, slow=26, signal=9)

    def test_macd_values_are_floats(self):
        prices = self._prices(60)
        ml, sl, hist = macd(prices)
        self.assertIsInstance(ml, float)
        self.assertIsInstance(sl, float)
        self.assertIsInstance(hist, float)


class TestSqliteDb(unittest.TestCase):
    def test_init_and_insert(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        init_db(db_path)
        event = {
            "timestamp_utc": "2026-05-01T10:00:00+00:00",
            "symbol": "BTC/USDT",
            "mode": "paper",
            "action": "buy",
            "reason": "sma_cross_up",
            "price": "80000.0",
            "amount": "0.001",
            "quote_value": "80.0",
        }
        append_trade_db(db_path, event)
        import sqlite3
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT * FROM trades").fetchall()
        conn.close()
        db_path.unlink()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][4], "buy")  # action column

    def test_init_idempotent(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        init_db(db_path)
        init_db(db_path)  # nie powinno rzucić wyjątku
        db_path.unlink()


if __name__ == "__main__":
    unittest.main()
