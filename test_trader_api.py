"""Testy dla trader_api.py (FastAPI)."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


class TestTraderApi(unittest.TestCase):
    def setUp(self):
        # Tworzymy tymczasowe pliki konfiguracji i stanu
        self.tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp_dir.name)

        self.state_file = tmp / "state.json"
        self.db_file = tmp / "trades.db"
        self.config_file = tmp / "cfg.json"

        cfg_data = {
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "timeframe": "1m",
            "fast_sma": 9,
            "slow_sma": 21,
            "quote_allocation": 50.0,
            "stop_loss_pct": 0.015,
            "take_profit_pct": 0.03,
            "poll_seconds": 15,
            "state_file": str(self.state_file),
            "trade_log_file": str(tmp / "trades.csv"),
            "db_file": str(self.db_file),
        }
        self.config_file.write_text(json.dumps(cfg_data))

        self.state_file.write_text(json.dumps({
            "position_open": False,
            "entry_price": 0.0,
            "amount": 0.0,
            "last_signal": "none",
            "updated_at": 0,
        }))

        # Inicjalizuj SQLite z jedną transakcją
        conn = sqlite3.connect(self.db_file)
        conn.execute("""CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT, symbol TEXT, mode TEXT,
            action TEXT, reason TEXT, price REAL,
            amount REAL, quote_value REAL)""")
        conn.execute("""INSERT INTO trades VALUES
            (1,'2026-05-01T10:00:00+00:00','BTC/USDT','paper','buy','sma_cross_up',80000,0.001,80)""")
        conn.commit()
        conn.close()

        import trader_api
        trader_api.CONFIG_PATH = self.config_file
        self.client = TestClient(trader_api.app)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_status(self):
        r = self.client.get("/status")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("position_open", data)
        self.assertFalse(data["position_open"])
        self.assertEqual(data["symbol"], "BTC/USDT")

    def test_trades(self):
        r = self.client.get("/trades")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["trades"][0]["action"], "buy")

    def test_trades_empty_when_no_db(self):
        self.db_file.unlink()
        r = self.client.get("/trades")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["trades"], [])


if __name__ == "__main__":
    unittest.main()
