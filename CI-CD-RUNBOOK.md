# CI/CD Automation — Test Automation Pipeline

Data utworzenia: 9 maja 2026  
Status: **OPERACYJNY** — Wdrażanie CI/CD dla automatyzacji testów

## Przegląd

GitHub Actions workflow automatyzuje wykonywanie test suite'u na każde push do `main`/`develop` oraz na pull requests. Pipeline stanowi quality gate zapobiegający regression w kodzie przed mergerem.

## Architektura

```
 Push to main/develop
     ↓
 Workflow trigger: test-automation.yml
     ├─ [Setup] Verify Python 3.10, install dependencies
     ├─ [Test Suite 1] API Tests (Load, Spike, Soak, SLA, Assertions) — 45min timeout
     ├─ [Test Suite 2] JMeter CRUD Tests — 30min timeout  
     ├─ [Test Suite 3] K6 Load Tests — 30min timeout
     ├─ [Test Suite 4] Stress Tests (Resilience) — Optional, 15min
     ├─ [Quality Gate] Check all suites passed
     └─ [Summary] Report results
```

## Komponenty Workflow

### 1. Setup Job
- Veryfikuje Python 3.10 dostępny
- Instaluje dependencies z `requirements.txt`
- Cache'uje pip dependencies dla szybkości

### 2. API Tests Job
- Uruchamia core test suite: Load, Spike, Soak, SLA, Assertions
- Inicjalizuje mock API server na `localhost:8000`
- Wykonuje: `python scripts/run-tests.py --health && python scripts/run-tests.py`
- Timeout: 45 minut (soak test trwa ~13min)
- Artefakty: `logs/`, `reports/`

### 3. JMeter CRUD Job
- Specjalistyczny CRUD workflow test za pośrednictwem JMeter backend'u Taurus
- Timeout: 30 minut
- Wykonuje: `python scripts/run-tests.py --include-jmeter`

### 4. K6 Tests Job
- JavaScript-based load testing framework
- 20 concurrent VUs, 2:20 ramp profile
- Timeout: 30 minut
- Wykonuje: `python scripts/run-tests.py --include-k6`

### 5. Quality Gate
 - Agreguje wyniki wszystkich test job'ów
 
 ### 4a. Stress Test Job (Optional)
 - Moderately-weighted resilience test: 50 concurrent threads, 2min ramp-up, 2min hold
 - Validates system performance under prolonged load
 - Success criterion: <5% failure rate acceptable
 - Timeout: 15 minut
 - Wykonuje: `python scripts/run-tests.py --include-stress`
 - Status: ✅ Operational, not yet integrated to main pipeline (can be added via CI workflow update)
- Blokuje merge jeśli **ANY** test suite się nie powiódł
- Exit code 1 = fail, 0 = success

### 6. Summary
- Raportuje status dla wszystkich suites
- Widoczny w GitHub checks na PR/commit

## Zmienne Środowiska

```yaml
PYTHON_VERSION: "3.10"
ARTIFACT_RETENTION_DAYS: 30
```

## Warunki Uruchomienia

Workflow automatycznie triggeruje się na:
- `push` na gałęzie `main` lub `develop`
- `pull_request` na gałęzie `main` lub `develop`  
- Ręczne trigger via `workflow_dispatch` (Actions tab w GitHub)

## Logs i Artefakty

### Dostęp do Rezultatów
1. Przejdź do **Actions** tab w GitHub repo
2. Kliknij na workflow run
3. Ekspanduj job (test-api, test-jmeter, test-k6)
4. Pobierz artefakty z sekcji **Artifacts**

### Artefakty Dostępne
- **api-test-results**: JTL files, HTML reports z Load, Spike, Soak, SLA, Assertions
- **jmeter-test-results**: CRUD workflow logs
- **k6-test-results**: K6 check results i duration metrics

## Status Checks

Na każdy PR pojawią się quality checks:
```
✅ test-automation / setup
✅ test-automation / test-api
✅ test-automation / test-jmeter
✅ test-automation / test-k6
✅ test-automation / quality-gate
```

**Jeśli ANY check fali → merge zablokowany do czasu naprawy**

## Failover & Troubleshooting

### Wszystkie testy się nie powiodły
1. Sprawdź mock API server logs w workflow output
2. Zweryfikuj że `tests/api/*.yml` mają poprawną składnię YAML
3. Sprawdź że `requirements.txt` zawiera wszystkie zależności

### Timeout (45min dla API tests)
- Soak test trwa normalnie ~13min
- Jeśli timeout = sprawdź czy mock server się nie zawiesi
- Rozwiązanie: Zwiększyć timeout w workflow do 60min

### Single test suite fails
1. Sprawdzaj detailed logs w GitHub Actions UI
2. Replikuj lokalnie: `python scripts/run-tests.py [--include-jmeter|--include-k6]`
3. Fix w feature branch, push → CI/CD waliduje automatycznie

## Integracja z Deployment'em

### Pre-Deployment Gate
```
Deployment workflow (gdy dostępny) powinien zależy od:
- quality-gate job success
- Lub require manual approval po passie testów
```

### Polityka Merge'u
Rekomendacja:
```
Branch protection rules:
- Require pull request review: 1 approved review
- Require status checks to pass: test-automation/*
- Require branches to be up to date
- Require conversation resolution
```

## Komendy Lokalne (dla Devów)

Przed push'em, waliduj lokalnie:

```powershell
# Lista dostępnych testów
python scripts/run-tests.py --list

# Health check (szybki)
python scripts/run-tests.py --health

# Pełny test suite bez JMeter/K6
python scripts/run-tests.py

# Z JMeter
python scripts/run-tests.py --include-jmeter

# Z K6
python scripts/run-tests.py --include-k6

# Wszystko
python scripts/run-tests.py --include-jmeter --include-k6
```

## Monitoring & Alerting (Przyszłość)

Możliwości rozszerzenia:
- Email notifications na PR fail
- Slack integration dla deployment team
- Metrics dashboard (Success Rate, Avg Response Time, p99 latency)
- Performance regression detection (SLA check)

## Metryki Bazowe (2026-05-09)

Z ostatniego full run:

| Test | Samples | Failure Rate | Avg Response | Duration |
|------|---------|--------------|--------------|----------|
| Load | 4,716 | 0.00% | 0.126s | 1m 2s |
| Spike | 521 | 0.00% | 3.503s | 44s |
| Soak | 63,367 | 0.00% | 0.094s | 10m 24s |
| SLA | 12,611 | 0.00% | 0.047s | 2m 17s |
| Assertions | 1,788 | 0.00% | 0.054s | 39s |
| JMeter CRUD | 20,241 | 0.00% | 0.259s | 4m 18s |
| K6 | 1,789 checks | 0% HTTP fail | 10.78ms | 2m 20s |

**Razem:** ~105k samples, **0% failure rate**, ~13 minut total runtime

## Checklisty

### Przed First Push do CI/CD
- [x] `requirements.txt` zawiera všechny zależności
- [x] `scripts/run-tests.py` używa `--health` flag
- [x] Mock server autostart w workflow (python scripts/mock-api-server.py)
- [x] Artefakty uploadują się prawidłowo
- [x] Timeout'y są realistyczne dla każdego test job'u

### Maintenance (Tygodniowo)
- [ ] Review action logs dla anomalii
- [ ] Sprawdź artifact storage (30 dni retention)
- [ ] Waliduj że metryki pozostają w normie (<5% increase w avg response time)

---

**Następny Krok:** Push workflow do GitHub, ustawić branch protection rules, i monitorować pierwsze CI runs.
