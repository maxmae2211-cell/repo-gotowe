# Przykład webhooka powiadamiającego o wygenerowaniu raportu
import requests
import os


def notify_webhook(report_path: str, webhook_url: str):
    with open(report_path, 'rb') as f:
        files = {'file': (os.path.basename(report_path), f, 'text/html')}
        response = requests.post(webhook_url, files=files)
        print(f"Status powiadomienia: {response.status_code}")

# Przykład użycia:
# notify_webhook('taurus-locust-report.html', 'https://your-webhook-url')
