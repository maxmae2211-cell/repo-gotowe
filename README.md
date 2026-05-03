# Taurus Test Project

Projekt przykładowy demonstrujący możliwości narzędzia Taurus do automatyzacji testów wydajności i funkcjonalnych.

## Instalacja

Taurus został już zainstalowany. Aby dodać katalog Scripts do PATH:

```powershell
$env:Path += ";C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts"
```

## Struktura projektu

- **test-api.yml** - Prosty test API (JSONPlaceholder)
- **test-support.yml** - Test dla środowiska support/production
- **test-locust.yml** - Scenariusz Taurus z executorem Locust
- **test-gatling.yml** - Scenariusz Taurus z executorem Gatling
- **test-k6.yml** - Scenariusz Taurus z executorem k6
- **test-robot.yml** - Scenariusz Taurus z executorem Robot Framework
- **test-selenium.py** - Test Selenium (wyszukiwanie Google)
- **test-selenium.yml** - Konfiguracja dla testu Selenium
- **test-advanced.yml** - Zaawansowana konfiguracja z wieloma scenariuszami

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

### Test 4: Pozostale scenariusze Taurus

```powershell
bzt test-locust.yml
bzt test-gatling.yml
bzt test-k6.yml
bzt test-robot.yml
bzt test-support.yml
```

W VS Code możesz też użyć gotowych tasków z `.vscode/tasks.json` oraz profili debug z `.vscode/launch.json` dla tych scenariuszy.

## Alternatywne narzędzia (poza Taurus)

Repo zawiera też konfiguracje do uruchamiania testów bezpośrednio przez inne narzędzia:

- `artillery.yml` + `npm run load:artillery`
- `examples/k6_example.js` + `npm run load:k6`
- `locustfile.py` + `npm run load:locust`

Przykłady uruchomień:

```powershell
# Artillery
npm run load:artillery

# k6
npm run load:k6

# Locust (UI na http://localhost:8089)
npm run load:locust
```

## Uruchamianie w kontenerze deweloperskim (VS Code Dev Containers)

Możesz uruchomić środowisko programistyczne w kontenerze:

1. Zainstaluj rozszerzenie **Dev Containers** w VS Code.
2. Otwórz ten folder w VS Code i wybierz opcję "Reopen in Container".
3. Kontener automatycznie zainstaluje zależności z `requirements.txt`.

W kontenerze masz dostępne:

- Pythona 3.11
- Taurus (po instalacji przez pip)
- Wszystkie narzędzia zdefiniowane w `requirements.txt`

Pliki konfiguracyjne znajdują się w `.devcontainer/`.

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

## Przydatne linki

- [Dokumentacja Taurus](https://gettaurus.org/docs/)
- [Schemat YAML](https://gettaurus.org/docs/YAMLStructure/)
- [JSONPlaceholder](https://jsonplaceholder.typicode.com/) - Testowy API
