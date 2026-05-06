# Setup Summary — repo-gotowe

## ✅ Co zostało skonfigurowane

### Narzędzia testowania wydajności
| Narzędzie | Konfiguracja | Status |
|-----------|-------------|--------|
| Taurus (BZT) | `test-api.yml`, `test-advanced.yml` | ✅ Gotowy |
| Locust | `test-locust.yml`, `test-locust.py` | ✅ Gotowy |
| k6 | `taurus-k6.yml` | ✅ Gotowy |
| Selenium | `test-selenium.yml`, `tests/ui/` | ✅ Gotowy |
| JMeter (przez Taurus) | `tests/api/test-api-jmeter.yml` | ✅ Gotowy |

### Struktura katalogów

```
repo-gotowe/
├── Konfiguracje testów (*.yml)     — scenariusze Taurus
├── Skrypty analizy (*.py)          — analiza wyników JTL/KPI
├── scripts/                        — automatyzacja
├── tests/api/                      — konfiguracje API testów
├── tests/ui/                       — konfiguracje UI testów
├── api/                            — lokalne API (FastAPI)
├── reports/                        — katalog raportów
└── docker-compose.yml              — stack Docker
```

### Środowisko Python
- **Wersja:** Python 3.10
- **Virtualenv:** `.venv-taurus/` lub `.venv/`
- **Kluczowe pakiety:** `bzt`, `flask`, `locust`, `selenium`, `requests`

### API testowe
- **Lokalne Flask API:** `app.py` na porcie 8000
- **Zewnętrzne API:** `https://jsonplaceholder.typicode.com`
- **Mock API:** `scripts/mock-api-server.py`

## 🔧 Konfiguracja (jak uruchomić od zera)

### 1. Instalacja zależności
```powershell
# Opcja A: przez batch
.\install_packages.bat

# Opcja B: ręcznie
python -m pip install bzt flask locust selenium requests
```

### 2. Weryfikacja instalacji
```powershell
bzt --version
python -c "import locust; print('Locust OK')"
python -c "import flask; print('Flask OK')"
```

### 3. Uruchomienie pierwszego testu
```powershell
bzt test-api.yml
```

### 4. Generowanie raportu
```powershell
python generate_report.py
```

## 📊 Wyniki testów

Po uruchomieniu testu Taurus tworzy katalog artefaktów w formacie `YYYY-MM-DD_HH-MM-SS.*`:
- `kpi.jtl` — surowe wyniki w formacie CSV
- `bzt.log` — log z testu
- `jmeter.log` — log JMeter

Skrypty analizy automatycznie wykrywają najnowszy katalog artefaktów.

## ⚙️ Zmienne środowiskowe

| Zmienna | Opis | Domyślnie |
|---------|------|-----------|
| `API_URL` | URL testowanego API | `http://localhost:8000` |
| `CONCURRENCY` | Liczba równoległych użytkowników | `10` |
| `HOLD_TIME` | Czas trwania testu | `2m` |

## 🔑 BlazeMeter (opcjonalnie)

Token konfiguruje się w `~/.bzt-rc`:
```yaml
modules:
  blazemeter:
    token: <twój_token>
    project: repo-gotowe
```

## 📝 Zmiany i naprawione błędy

### v1.1 (aktualna)
- ✅ Naprawiono hardcodowane ścieżki w `analyze_results.py`, `analyze-kpi.py`, `generate_html_report.py`, `generate_report.py`
- ✅ Naprawiono hardcodowane ścieżki użytkownika w `run-api.ps1`, `run-all.ps1`
- ✅ Naprawiono `install_packages.bat` — poprawna ścieżka + wszystkie pakiety
- ✅ Zaktualizowano `package.json` — rzeczywiste skrypty testowe
- ✅ Dodano fallback dla `.venv-taurus` w `scripts/run-all-tests.ps1`
- ✅ Uzupełniono `README.md` i `SETUP-SUMMARY.md`
