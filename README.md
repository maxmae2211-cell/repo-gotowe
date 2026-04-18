# Taurus Test Project

Projekt przykładowy demonstrujący możliwości narzędzia Taurus do automatyzacji testów wydajności i funkcjonalnych.

## Instalacja

Taurus został już zainstalowany. Aby dodać katalog Scripts do PATH:

```powershell
$env:Path += ";C:\Users\maxma\AppData\Roaming\Python\Python311\Scripts"
```

## Struktura projektu

- **test-api.yml** - Prosty test API (JSONPlaceholder)
- **test-advanced.yml** - Zaawansowana konfiguracja z wieloma scenariuszami
- **test-locust.yml** - Konfiguracja testu Locust
- **test-selenium.yml** - Konfiguracja dla testu Selenium
- **analyze_kpi.py** - Analiza KPI z pliku JTL (z bramką jakości)
- **analyze_results.py** - Szczegółowa analiza wyników per endpoint
- **generate_report.py** - Generowanie zbiorczego raportu HTML
- **run_pipeline.py** - Orkiestrator pełnego pipeline'u analizy (uruchamia kolejno: analyze_kpi → analyze_results → generate_report)
- **jtl_metrics.py** - Wspólne funkcje do odczytu i agregacji metryk JTL
- **scripts/run-taurus.ps1** - Skrypt PowerShell do uruchamiania Taurusa w różnych trybach
- **crypto_auto_trader.py** - Autonomiczny trader kryptowalut oparty na strategii SMA (domyślnie paper trading)
- **backtest_trader.py** - Backtesting strategii tradera na danych historycznych

## Uruchomienie testów

### Test 1: Prosty test API
```powershell
bzt test-api.yml
```

### Test 2: Test wśród wiele scenariuszy
```powershell
bzt test-advanced.yml
```

### Test 3: Test Selenium (wymaga ChromeDriver)
```powershell
# Najpierw zainstaluj Selenium
pip install selenium --user

# Pobierz ChromeDriver z https://chromedriver.chromium.org/
# i umieść w katalogu projektu lub dodaj do PATH

# Uruchom test
bzt test-selenium.yml
```

## Pipeline analizy wyników

Po uruchomieniu testów uruchom pełny pipeline analizy:

```powershell
# Automatyczne wykrywanie najnowszych artefaktów Taurus
python run_pipeline.py

# Z konkretnym plikiem JTL
python run_pipeline.py --jtl 2026-04-18_12-00-00.000000/kpi.jtl

# Z bramką jakości (max 0 błędów, max 200ms średni czas)
python run_pipeline.py --max-failures 0 --max-avg-ms 200
```

Raport HTML zostanie zapisany jako `taurus-locust-report.html`.

## Crypto Auto Trader

Autonomiczny trader kryptowalut z domyślnym trybem paper trading:

```powershell
# Paper trading (symulacja, bez realnych zleceń)
python crypto_auto_trader.py --config trader_config.example.json

# Backtesting na danych historycznych
python backtest_trader.py --config trader_config.example.json
```

> **Uwaga:** Tryb live wymaga flagi `--live` i kluczy API w pliku konfiguracji.
> Plik `trader_config.json` jest ignorowany przez Git (`.gitignore`).

## Dostępne opcje

```powershell
# Verbose mode (więcej informacji)
bzt -v test-api.yml

# Override opcji konfiguracji
bzt -o execution.0.concurrency=20 test-api.yml

# Quiet mode (mniej informacji)
bzt -q test-api.yml
```

## Generowanie raportów

Po uruchomieniu testów, Taurus automatycznie generuje raporty. Aby je przeglądać:

```powershell
# Test wygeneruje raport HTML
# Lokalizacja: .taurus/ folder
```

## Zmienne konfiguracyjne

- **concurrency** - Liczba użytkowników jednocześnie
- **hold-for** - Jak długo trzymać obciążenie (10s, 1m, 2m itd.)
- **ramp-up** - Czas rozwijania obciążenia
- **throughput** - Liczba requestów na sekundę

## Testy jednostkowe

```powershell
pip install pytest
pytest tests/ -v
```

## CI/CD

Repozytorium zawiera workflow GitHub Actions (`.github/workflows/taurus-ci.yml`), który:
1. Instaluje zależności Python
2. Uruchamia testy jednostkowe (`pytest tests/`)
3. Uruchamia pipeline analizy na przykładowym pliku JTL (`tests/fixtures/sample.jtl`)
4. Publikuje raport HTML jako artefakt GitHub Actions

## Przydatne linki

- [Dokumentacja Taurus](https://gettaurus.org/docs/)
- [Schemat YAML](https://gettaurus.org/docs/YAMLStructure/)
- [JSONPlaceholder](https://jsonplaceholder.typicode.com/) - Testowy API

