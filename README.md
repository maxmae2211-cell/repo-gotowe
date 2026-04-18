# Taurus Test Project

Projekt przykładowy demonstrujący możliwości narzędzia Taurus do automatyzacji testów wydajności i funkcjonalnych.

## Instalacja

Taurus został już zainstalowany. Aby dodać katalog Scripts do PATH:

```powershell
$env:Path += ";C:\Users\maxma\AppData\Roaming\Python\Python311\Scripts"
```

## Struktura projektu

- **test-api.yml** - Prosty test API (JSONPlaceholder)
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
