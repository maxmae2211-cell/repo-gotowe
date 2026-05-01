FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Domyślnie uruchamia tradera w trybie paper
# Aby użyć live: docker run -e EXCHANGE_API_KEY=... -e EXCHANGE_API_SECRET=... ... --live
ENV PYTHONUNBUFFERED=1
CMD ["python3", "crypto_auto_trader.py", "--config", "trader_config.json"]
