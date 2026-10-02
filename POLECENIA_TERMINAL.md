# Najważniejsze polecenia terminalowe dla repozytorium "repo-gotowe"

## 1. Aktywacja środowiska wirtualnego (PowerShell)

```
.venv\Scripts\Activate.ps1
```

lub

```
& .venv\Scripts\Activate.ps1
```

## 2. Instalacja zależności

```
pip install -r requirements.txt
```

## 3. Uruchomienie głównego skryptu

```
python main.py
```

## 4. Uruchomienie testów Taurus (API)

```
bzt test-api.yml
```

## 5. Uruchomienie testów Taurus (zaawansowane)

```
bzt test-advanced.yml
```

## 6. Sprawdzenie statusu GIT

```
git status
```

## 7. Dodanie i commit zmian

```
git add -A
git commit -m "Twój opis commita"
```

## 8. Wysłanie zmian na GitHub

```
git push
```

---

Jeśli chcesz uruchomić inne testy (np. Selenium), napisz – podam dokładne polecenie.
