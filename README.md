# Dokumentacja projektu repo-gotowe

[![CI](https://github.com/maxmae2211-cell/repo-gotowe/actions/workflows/ci.yml/badge.svg)](https://github.com/maxmae2211-cell/repo-gotowe/actions/workflows/ci.yml)
[![Taurus Tests](https://github.com/maxmae2211-cell/repo-gotowe/actions/workflows/taurus.yml/badge.svg)](https://github.com/maxmae2211-cell/repo-gotowe/actions/workflows/taurus.yml)

## Opis

Repozytorium automatyzuje testy wydajnoĹ›ciowe, generowanie raportĂłw HTML, analizÄ™ wynikĂłw, powiadomienia i integracjÄ™ z CI/CD.

## Szybki start

1. Zainstaluj zaleĹĽnoĹ›ci: `pip install -r requirements.txt`
2. Uruchom testy: `pytest`
3. Wygeneruj raport: `python generate_report.py --output taurus-locust-report.html`
4. Wygeneruj wykresy: `python plot_response_times.py <plik_jtl> <katalog_wyjsciowy>`
5. WyĹ›lij powiadomienie: `python notify_webhook.py`

## Automatyzacja

- Workflow GitHub Actions: `.github/workflows/generate-report.yml`
- Automatyczne powiadomienia: `notify_webhook.py`
- Analiza wynikĂłw: `plot_response_times.py`

## Testy

- `test_generate_report.py` â€” testuje generowanie raportu HTML

## Autorzy

- ZespĂłĹ‚ repo-gotowe

## Taurus Test Project

Projekt przykĹ‚adowy demonstrujÄ…cy moĹĽliwoĹ›ci narzÄ™dzia Taurus do automatyzacji testĂłw wydajnoĹ›ci i funkcjonalnych.

## Instalacja

Taurus zostaĹ‚ juĹĽ zainstalowany. Aby dodaÄ‡ katalog Scripts do PATH:

```powershell
$env:Path += ";C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts"
```

## Struktura projektu

- **test-api.yml** - Prosty test API (JSONPlaceholder)
- **test-support.yml** - Test dla Ĺ›rodowiska support/production
- **test-locust.yml** - Scenariusz Taurus z executorem Locust
- **test-gatling.yml** - Scenariusz Taurus z executorem Gatling
- **test-k6.yml** - Scenariusz Taurus z executorem k6
- **test-robot.yml** - Scenariusz Taurus z executorem Robot Framework
- **test-selenium.py** - Test Selenium (wyszukiwanie Google)
- **test-selenium.yml** - Konfiguracja dla testu Selenium
- **test-advanced.yml** - Zaawansowana konfiguracja z wieloma scenariuszami

## Uruchomienie testĂłw

### Test 1: Prosty test API

```powershell
bzt test-api.yml
```

### Test 2: Test wĹ›rĂłd wiele scenariuszy

```powershell
bzt test-advanced.yml
```

### Test 3: Test Selenium (wymaga ChromeDriver)

```powershell
# Najpierw zainstaluj Selenium
pip install selenium --user

# Pobierz ChromeDriver z https://chromedriver.chromium.org/
# i umieĹ›Ä‡ w katalogu projektu lub dodaj do PATH

# Uruchom test
bzt test-selenium.yml
```

### Test 4: Pozostale scenariusze Taurus

```powershell
bzt test-locust.yml
bzt test-gatling.yml
bzt test-k6.yml
bzt test-robot.yml
bzt test-support.yml
```

W VS Code moĹĽesz teĹĽ uĹĽyÄ‡ gotowych taskĂłw z `.vscode/tasks.json` oraz profili debug z `.vscode/launch.json` dla tych scenariuszy.

## Alternatywne narzÄ™dzia (poza Taurus)

Repo zawiera teĹĽ konfiguracje do uruchamiania testĂłw bezpoĹ›rednio przez inne narzÄ™dzia:

- `artillery.yml` + `npm run load:artillery`
- `examples/k6_example.js` + `npm run load:k6`
- `locustfile.py` + `npm run load:locust`

PrzykĹ‚ady uruchomieĹ„:

```powershell
# Artillery
npm run load:artillery

# k6
npm run load:k6

# Locust (UI na http://localhost:8089)
npm run load:locust
```

## Uruchamianie w kontenerze deweloperskim (VS Code Dev Containers)

MoĹĽesz uruchomiÄ‡ Ĺ›rodowisko programistyczne w kontenerze:

1. Zainstaluj rozszerzenie **Dev Containers** w VS Code.
2. OtwĂłrz ten folder w VS Code i wybierz opcjÄ™ "Reopen in Container".
3. Kontener automatycznie zainstaluje zaleĹĽnoĹ›ci z `requirements.txt`.

W kontenerze masz dostÄ™pne:

- Pythona 3.11
- Taurus (po instalacji przez pip)
- Wszystkie narzÄ™dzia zdefiniowane w `requirements.txt`

Pliki konfiguracyjne znajdujÄ… siÄ™ w `.devcontainer/`.

## DostÄ™pne opcje

```powershell
# Verbose mode (wiÄ™cej informacji)
bzt -v test-api.yml

# Override opcji konfiguracji
bzt -o execution.0.concurrency=20 test-api.yml

# Quiet mode (mniej informacji)
bzt -q test-api.yml
```

## Generowanie raportĂłw

Po uruchomieniu testĂłw, Taurus automatycznie generuje raporty. Aby je przeglÄ…daÄ‡:

```powershell
# Test wygeneruje raport HTML
# Lokalizacja: .taurus/ folder
```

## Zmienne konfiguracyjne

- **concurrency** - Liczba uĹĽytkownikĂłw jednoczeĹ›nie
- **hold-for** - Jak dĹ‚ugo trzymaÄ‡ obciÄ…ĹĽenie (10s, 1m, 2m itd.)
- **ramp-up** - Czas rozwijania obciÄ…ĹĽenia
- **throughput** - Liczba requestĂłw na sekundÄ™

## Agent Inspector (AI Toolkit)

Projekt integruje siÄ™ z VS Code AI Toolkit Agent Inspector przez `src/agent.py`.

**Wymagania:** `pip install debugpy agent-dev-cli fastapi uvicorn`

**Uruchomienie lokalnie:**

```powershell
python -m debugpy --listen 127.0.0.1:5679 -m agentdev run src/agent.py --verbose --port 8088 -- --server
```

**DostÄ™pne endpointy HTTP:**

- `GET /health` â€” status serwera
- `GET /results` â€” ostatnie wyniki testu
- `POST /run` â€” uruchom test (`{"config": "api", "mode": "standard"}`)

**VS Code:** UĹĽyj konfiguracji `Agent Inspector: Debug HTTP Server` w `launch.json`.

## Docker (lokalny dev)

```powershell
# Uruchom serwer agenta
docker compose up agent

# Uruchom testy
docker compose run tests
```

## Azure Functions

Plik `host.json` konfiguruje Ĺ›rodowisko uruchomieniowe Azure Functions v2 z Application Insights sampling
i rozszerzeniem bundle `Microsoft.Azure.Functions.ExtensionBundle v4.*`.
Konfiguracja lokalna: `local.settings.json` (nie commituj do repo â€” jest w `.gitignore`).

## Przydatne linki

- [Dokumentacja Taurus](https://gettaurus.org/docs/)
- [Schemat YAML](https://gettaurus.org/docs/YAMLStructure/)
- [JSONPlaceholder](https://jsonplaceholder.typicode.com/) - Testowy API
- [BlazeMeter Dashboard](https://a.blazemeter.com/app/#/accounts/2190559/workspaces/2269510/dashboard)
- [AI Toolkit for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-windows-ai-studio.windows-ai-studio)

