# repo-gotowe — Infrastruktura Testów Wydajnościowych

Kompleksowa infrastruktura do testowania wydajności API i aplikacji webowych przy użyciu **Taurus (BZT)**, **k6**, **Locust** i **Selenium**.

## 🚀 Szybki Start

```powershell
# 1. Uruchom podstawowy test API
bzt test-api.yml

# 2. Uruchom zaawansowany test
bzt test-advanced.yml -v

# 3. Test z Locust
bzt test-locust.yml

# 4. Wygeneruj raport
python generate_report.py
```

## 📁 Struktura projektu

```
repo-gotowe/
├── app.py                    # Lokalne API Flask (test target)
├── test-api.yml              # Scenariusz testów API (Taurus/JMeter)
├── test-advanced.yml         # Zaawansowane testy (ramp-up, asercje)
├── test-locust.yml           # Konfiguracja testów Locust przez Taurus
├── test-locust.py            # Scenariusz Locust (Python)
├── test-selenium.yml         # Testy UI Selenium
├── taurus-k6.yml             # Testy k6 przez Taurus
├── analyze_results.py        # Analiza wyników JTL
├── analyze-kpi.py            # Analiza KPI z pliku kpi.jtl
├── generate_report.py        # Raport HTML podsumowujący
├── generate_html_report.py   # Szczegółowy raport HTML
├── scripts/                  # Skrypty automatyzujące
│   ├── run-all-tests.ps1     # Uruchomienie wszystkich testów
│   ├── mock-api-server.py    # Lokalne mock API do testów
│   └── ...
├── tests/
│   ├── api/                  # Konfiguracje testów API
│   └── ui/                   # Konfiguracje testów UI
└── docker-compose.yml        # Docker stack
```

## 🛠 Wymagania

- Python 3.10+
- Taurus BZT: `pip install bzt`
- Flask: `pip install flask`
- Locust: `pip install locust`

Lub zainstaluj wszystko przez:
```batch
install_packages.bat
```

## 🧪 Uruchamianie testów

### Test API (Taurus/JMeter)
```powershell
bzt test-api.yml
```

### Test zaawansowany z ramp-up
```powershell
bzt test-advanced.yml -v
```

### Test Locust
```powershell
bzt test-locust.yml
# lub
locust -f test-locust.py --headless --users 10 --spawn-rate 2 --run-time 1m --host https://jsonplaceholder.typicode.com
```

### Wszystkie testy (ze skryptem)
```powershell
.\scripts\run-all-tests.ps1 -Verbose
```

## 📊 Analiza wyników

Po uruchomieniu testu Taurus tworzy katalog artefaktów `YYYY-MM-DD_HH-MM-SS.*` z plikiem `kpi.jtl`.

```powershell
# Analiza KPI (automatycznie znajdzie ostatni test)
python analyze-kpi.py

# Pełna analiza statystyczna
python analyze_results.py

# Generowanie raportu HTML
python generate_html_report.py
# Wynik: taurus-analysis-report.html

# Kompletny raport HTML
python generate_report.py
# Wynik: taurus-locust-report.html
```

## 🌐 Lokalne API

```powershell
# Uruchom lokalne Flask API
python app.py
# Dostępne na http://localhost:8000

# Endpointy:
# GET  http://localhost:8000/get
# POST http://localhost:8000/post
```

## 📖 Dokumentacja

- [QUICKSTART.md](QUICKSTART.md) — Szybki start krok po kroku
- [CONCEPTS.md](CONCEPTS.md) — Podstawowe pojęcia Taurus
- [SETUP-SUMMARY.md](SETUP-SUMMARY.md) — Podsumowanie konfiguracji

## 📝 Konfiguracja testów

Pliki konfiguracyjne YAML używają formatu Taurus:
```yaml
execution:
  - concurrency: 10
    hold-for: 2m
    ramp-up: 30s
    scenario: my_scenario

scenarios:
  my_scenario:
    requests:
      - url: http://localhost:8000/get
        method: GET
        assert:
          - contains: "OK"
```

## 🐳 Docker

```powershell
docker-compose up -d
```
