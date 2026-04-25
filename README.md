
# Taurus Test Project

![CI](https://github.com/maxmae2211-cell/repo-gotowe/actions/workflows/taurus.yml/badge.svg?branch=backup/qq-before-fix)
![Lint](https://img.shields.io/badge/lint-flake8-blue)
![Testy](https://img.shields.io/badge/tests-pytest-green)
![Bezpieczeństwo](https://img.shields.io/badge/security-bandit-yellow)
![Formatowanie](https://img.shields.io/badge/format-black-black)
![Coverage](https://img.shields.io/badge/coverage-auto-informational)

Projekt przykładowy demonstrujący możliwości narzędzia Taurus do automatyzacji testów wydajności i funkcjonalnych.

## Instalacja

Taurus został już zainstalowany. Aby dodać katalog Scripts do PATH:

```powershell
$env:Path += ";C:\Users\maxma\AppData\Roaming\Python\Python311\Scripts"
```

## Struktura projektu

- **test-api.yml** – Prosty test API (JSONPlaceholder)
- **test-moj.yml** – Przykładowy test POST/GET na użytkownikach (JSONPlaceholder)
- **test-advanced.yml** – Zaawansowana konfiguracja z wieloma scenariuszami
- **test-selenium.yml** – Konfiguracja dla testu Selenium
- **test-selenium.py** – Test Selenium (przykład: wyszukiwanie Google)

## Uruchomienie testów

### Test 1: Prosty test API

```powershell
bzt test-api.yml
```

### Test 2: Test własny (POST/GET użytkownicy)

```powershell
bzt test-moj.yml
```

### Test 3: Test zaawansowany (wiele scenariuszy)

```powershell
bzt test-advanced.yml
```

### Test 4: Test Selenium (wymaga ChromeDriver)

```powershell
# Najpierw zainstaluj Selenium
pip install selenium --user

# Pobierz ChromeDriver z https://chromedriver.chromium.org/
# i umieść w katalogu projektu lub dodaj do PATH

# Przykładowy plik test-selenium.py znajdziesz w repozytorium

# Uruchom test
bzt test-selenium.yml
```

## Dostępne opcje

```powershell
# Verbose mode (więcej informacji)
bzt -v test-api.yml

# Override opcji konfiguracji
bzt -o execution.0.concurrency=20 test-api.yml

# Quiet mode (mniej informacji)
bzt -q test-api.yml
```

## CI/CD – Automatyczne testy Taurus

Testy Taurus uruchamiają się automatycznie na GitHub Actions przy każdym commicie i pull requeście (gałęzie main, backup/qq-before-fix). Wyniki znajdziesz w zakładce **Actions** na GitHubie.

## Generowanie raportów

Po uruchomieniu testów, Taurus automatycznie generuje raporty HTML. Lokalizacja: katalog .taurus/ lub katalog roboczy testu.

## Zmienne konfiguracyjne

- **concurrency** - Liczba użytkowników jednocześnie
- **hold-for** - Jak długo trzymać obciążenie (10s, 1m, 2m itd.)
- **ramp-up** - Czas rozwijania obciążenia
- **throughput** - Liczba requestów na sekundę

## Przydatne linki

- [Dokumentacja Taurus](https://gettaurus.org/docs/)
- [Schemat YAML](https://gettaurus.org/docs/YAMLStructure/)
- [JSONPlaceholder](https://jsonplaceholder.typicode.com/) - Testowy API
