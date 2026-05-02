# AutoAgent — Skill instrukcji operacyjnych

Skill dla autonomicznego agenta operacyjnego repo-gotowe.
Używaj gdy: taurus pipeline, bzt workflow, runbook sync, auto agent operacje, deploy testy, git operacje, przeglądarka automatyzacja.

## Komendy operacyjne

### Git
```powershell
# Status
git -C C:\Users\maxma\Documents\GitHub\repo-gotowe status

# Commit + push
git -C C:\Users\maxma\Documents\GitHub\repo-gotowe add -A
git -C C:\Users\maxma\Documents\GitHub\repo-gotowe commit -m "Opis zmian"
git -C C:\Users\maxma\Documents\GitHub\repo-gotowe push origin main
```

### Taurus
```powershell
# Health check
powershell -File scripts/run-taurus.ps1 -Mode health

# Standard test
powershell -File scripts/run-taurus.ps1 -Mode standard

# JMeter + Java8
powershell -File scripts/run-taurus.ps1 -Mode jmeter-java8

# Pełny potok
powershell -File scripts/run-taurus.ps1 -Mode pipeline
```

### Python
```powershell
C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe skrypt.py
```

## Etapy standardowego pipeline Taurus

1. Health check (`health`) — weryfikacja środowiska
2. Standard run (`standard`) — test z `test-api.yml`
3. JMeter run (`jmeter-java8`) — test z Java8
4. Analiza wyników (`analyze_results.py`)
5. Generowanie raportu (`generate_report.py`)
6. Commit + push wyników

## Obsługa błędów

- Jeśli `bzt` nie startuje → sprawdź `pip install bzt --upgrade`
- Jeśli 401 BlazeMeter → sprawdź `~/.bzt-rc`, format tokenu: `id:secret`
- Jeśli Java nie znaleziona → uruchom task "Windows: Zainstaluj wymagania systemowe"
- Jeśli test failuje → sprawdź logi w katalogu `artifacts/` lub katalog z timestampem

## Struktura repo

```
repo-gotowe/
├── scripts/
│   └── run-taurus.ps1          # Główny wrapper Taurus
├── test-api.yml                 # Standardowy test API
├── test-advanced.yml            # Test zaawansowany
├── test-support.yml             # Środowisko Support/Produkcja
├── test-locust.yml              # Test Locust
├── analyze_results.py           # Analiza wyników
├── generate_report.py           # Generowanie raportów
├── RUNBOOK-TAURUS.md            # Runbook operacyjny
├── README.md                    # Dokumentacja główna
└── .github/
    ├── agents/
    │   └── auto-agent.agent.md  # Ten agent
    └── skills/
        └── auto-agent/
            └── SKILL.md         # Ten skill
```

## BlazeMeter integracja

Token jest w `~/.bzt-rc` (poza repo — bezpiecznie).
Link do wyników: `https://a.blazemeter.com/app/#/accounts/2190559/workspaces/2269510/dashboard`

Aby sprawdzić wyniki ostatniego testu — otwórz powyższy link w przeglądarce.
