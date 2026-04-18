# Quick Start - Szybki Start z Taurus

## Krok 1: Przygotowanie PATH

```powershell
$env:Path += ";C:\Users\maxma\AppData\Roaming\Python\Python311\Scripts"
```

## Krok 2: Uruchomienie pierwszego testu

Najprostszy test API:

```powershell
bzt test-api.yml
```

Czekaj aż test się zakończy. Zobaczysz:
- Postęp testowania w realu
- Liczbę requestów
- Czasy odpowiedzi
- Błędy (jeśli jakieś będą)

## Krok 3: Bardziej zaawansowany test

```powershell
bzt test-advanced.yml -v
```

Flaga `-v` pokazuje więcej szczegółów (verbose).

## Krok 4: Test z Locust

Najpierw zainstaluj Locust:

```powershell
pip install locust --user
```

Następnie uruchom:

```powershell
bzt test-locust.yml
```

## Poglądowe komendy

### Zmień liczbę użytkowników dynamicznie:

```powershell
bzt -o execution.0.concurrency=20 test-api.yml
```

### Zmień czas trwania testu:

```powershell
bzt -o execution.0.hold-for=5m test-api.yml
```

### Pokaż wszystkie logi:

```powershell
bzt -v test-api.yml
```

### Zminimalizuj output (tylko błędy):

```powershell
bzt -q test-api.yml
```

## Gdzie najcz częściej się robi błędy?

1. **Zły URL** - upewnij się że API jest dostępne
2. **Brak certyfikatu SSL** - dodaj `disable: true` do ustawień SSL
3. **Timeout** - zmień w konfiguracji `timeout: 30`
4. **Zły format YAML** - indentation musi być poprawna (spacje, nie taby!)

## Przydatne opcje w YAML

```yaml
# Timeout dla requestu
timeout: 30

# Retry przy błędzie
retry-on-4xx: true
retry-on-5xx: true
retrieve-resources: true  # Pobierz zasoby CSS/JS

# User-Agent
headers:
  User-Agent: Taurus/1.16

# Cookie
cookies:
  session_id: abc123
```

## Generowanie HTML Raportu

Po uruchomieniu testu, raport html jest w folder `.taurus/`:

```powershell
# Otwórz folder
explorer .taurus
```

## Następne kroki

1. Czytaj dokumentację: https://gettaurus.org/docs/
2. Stwórz test dla Twojej aplikacji
3. Zautomatyzuj testy w CI/CD pipeline
4. Monitoruj trendy wydajności w czase

## Szybki hack

Jeśli test się wiesza, naciśnij:

```
Ctrl+C
```

Aby je zatrzymać.
