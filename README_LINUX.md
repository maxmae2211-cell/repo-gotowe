# Instrukcja uruchamiania na Linux/WSL

1. Zainstaluj zależności:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Uruchom pipeline testów:
   ```bash
   python3 run_pipeline.py
   ```
3. (Opcjonalnie) Budowa i uruchomienie przez Docker:
   ```bash
   docker build -t taurus-pipeline .
   docker run --rm taurus-pipeline
   ```
4. Testy jednostkowe i walidacja konfiguracji:
   ```bash
   python3 -m unittest
   ```
