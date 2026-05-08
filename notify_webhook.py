# Powiadomienia: webhook HTTP i Telegram bot
import os
import requests


def notify_webhook(report_path: str, webhook_url: str) -> int:
    """Wysyła raport HTML jako plik do webhooka (np. Slack, Teams)."""
    with open(report_path, "rb") as f:
        files = {"file": (os.path.basename(report_path), f, "text/html")}
        response = requests.post(webhook_url, files=files)
        print(f"Status powiadomienia webhook: {response.status_code}")
        return response.status_code


def notify_telegram(message: str, token: str = "", chat_id: str = "") -> int:
    """Wysyła wiadomość tekstową przez Telegram Bot API.

    Zmienne środowiskowe (fallback):
        TELEGRAM_BOT_TOKEN  — token bota z @BotFather
        TELEGRAM_CHAT_ID    — ID czatu/kanału (np. -100...)

    Przykład użycia:
        notify_telegram("BUY BTC/USDT @ 78000")
    """
    token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("TELEGRAM: brak TELEGRAM_BOT_TOKEN lub TELEGRAM_CHAT_ID — pominięto")
        return 0
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status powiadomienia Telegram: {response.status_code}")
    return response.status_code


# Przykład użycia:
# notify_webhook('taurus-locust-report.html', 'https://your-webhook-url')
# notify_telegram('Test wiadomości', token='...', chat_id='...')
