"""Testy jednostkowe dla notify_webhook.py"""
import notify_webhook
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open

sys.path.insert(0, os.path.dirname(__file__))


class TestNotifyWebhook(unittest.TestCase):

    def test_notify_webhook_sends_file(self):
        mock_response = MagicMock(status_code=200)
        with patch("notify_webhook.requests.post", return_value=mock_response) as mock_post:
            with patch("builtins.open", mock_open(read_data=b"<html/>")):
                result = notify_webhook.notify_webhook(
                    "report.html", "http://fake-url/hook")
        self.assertEqual(result, 200)
        mock_post.assert_called_once()

    def test_notify_telegram_no_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            # bez tokena/chat_id → zwraca 0, nie rzuca wyjątku
            result = notify_webhook.notify_telegram(
                "test", token="", chat_id="")
        self.assertEqual(result, 0)

    def test_notify_telegram_sends_message(self):
        mock_response = MagicMock(status_code=200)
        with patch("notify_webhook.requests.post", return_value=mock_response) as mock_post:
            result = notify_webhook.notify_telegram(
                "Hej", token="tok123", chat_id="42")
        self.assertEqual(result, 200)
        args, kwargs = mock_post.call_args
        self.assertIn("tok123", args[0])
        self.assertEqual(kwargs["json"]["text"], "Hej")

    def test_notify_telegram_uses_env_vars(self):
        mock_response = MagicMock(status_code=200)
        env = {"TELEGRAM_BOT_TOKEN": "envtok", "TELEGRAM_CHAT_ID": "99"}
        with patch.dict(os.environ, env):
            with patch("notify_webhook.requests.post", return_value=mock_response) as mock_post:
                notify_webhook.notify_telegram("env test")
        mock_post.assert_called_once()

    def test_notify_trader_signal_buy(self):
        with patch("notify_webhook.notify_telegram") as mock_tel:
            notify_webhook.notify_trader_signal(
                "buy", "BTC/USDT", 80000.0, 45.0)
        mock_tel.assert_called_once()
        msg = mock_tel.call_args[0][0]
        self.assertIn("BUY", msg)
        self.assertIn("BTC/USDT", msg)
        self.assertIn("80000.00", msg)

    def test_notify_trader_signal_sell(self):
        with patch("notify_webhook.notify_telegram") as mock_tel:
            notify_webhook.notify_trader_signal(
                "sell", "ETH/USDT", 3000.0, 75.0)
        mock_tel.assert_called_once()
        msg = mock_tel.call_args[0][0]
        self.assertIn("SELL", msg)

    def test_notify_trader_signal_hold_skipped(self):
        with patch("notify_webhook.notify_telegram") as mock_tel:
            notify_webhook.notify_trader_signal(
                "hold", "BTC/USDT", 80000.0, 50.0)
        mock_tel.assert_not_called()

    def test_notify_trader_signal_none_skipped(self):
        with patch("notify_webhook.notify_telegram") as mock_tel:
            notify_webhook.notify_trader_signal(
                "none", "BTC/USDT", 80000.0, 50.0)
        mock_tel.assert_not_called()


if __name__ == "__main__":
    unittest.main()
