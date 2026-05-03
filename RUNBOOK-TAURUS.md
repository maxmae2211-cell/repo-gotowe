# Taurus Runbook (verified on 2026-05-03)

This file captures the currently verified way to run this workspace on Windows.

## Latest verified pipeline results

- Standard API run: PASS (6565 samples, 0.00% failures, duration 3:04) -> Artifacts: `2026-05-02_22-36-07.933700`
- JMeter + Java8 run: PASS (6579 samples, 0.00% failures, duration 3:12) -> Artifacts: `2026-05-02_22-40-01.825186`
- Latest JMeter validation: PASS (6685 samples, 0.00% failures, average total time 0.086s) -> Artifacts: `2026-05-03_03-27-51.349996`

## Verified environment

- Python venv: `.venv`
- Taurus: `1.16.49`
- Setuptools in venv: `79.0.1`
- PyYAML in venv: `6.0.3`
- Manual JMeter available locally: `tools/apache-jmeter-5.6.3`
- Local Java 8 for compatibility runs: `tools/jdk8u482-b08`

## Fast health check

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"

c:/Users/maxma/Documents/GitHub/repo-gotowe/.venv/Scripts/python.exe -V
c:/Users/maxma/Documents/GitHub/repo-gotowe/.venv/Scripts/python.exe -m pip show bzt setuptools pyyaml
c:/Users/maxma/Documents/GitHub/repo-gotowe/.venv/Scripts/python.exe -m pip check
c:/Users/maxma/Documents/GitHub/repo-gotowe/.venv/Scripts/bzt.exe -h
```

## Standard API run

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"
c:/Users/maxma/Documents/GitHub/repo-gotowe/.venv/Scripts/bzt.exe test-api.yml
```

Expected: run finishes with exit code `0`, failures `0.00%`.

## Forced JMeter + Java 8 run

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"
./scripts/run-taurus.ps1 -Mode jmeter-java8
```

Skrypt używa lokalnego `tools/jdk8u482-b08`, a gdy lokalna Java jest niekompletna, przełącza się na systemowe `java` z `PATH`.
Use `execution.0.executor=jmeter` (indexed path), not `execution.executor=jmeter`.

## Git hygiene used in this repo

- `tools/` is ignored in `.gitignore`.
- `jmeter.log` is intentionally not tracked.
- Generated Taurus artifact folders are ignored via timestamp pattern.

## AI-only policy (zakaz recznego uruchamiania)

**Testy Taurus w tym repozytorium wolno uruchamiac WYLACZNIE przez AI lub automatyzacje.**

- Zabrania sie recznego uruchamiania testow przez czlowieka bez asysty AI.
- Kazde uruchomienie jest chronione mutexem `Global\repo-gotowe-taurus-single-run` — rownolegly run zostanie odrzucony z bledem.
- Zamiast `bzt` bezposrednio, zawsze uzyj: `scripts/run-taurus.ps1` (przez AI lub task VS Code).
- Jezeli chcesz uruchamiac z wielu okien, przekaz parametr `-AllowParallel` (tylko za zgoda AI).

**Dlaczego?** Rownolegly Taurus zatrzymuje komputer (brak limitu CPU/RAM). Mutex gwarantuje porzadek.

## Troubleshooting notes

- Taurus update-check 5xx warnings are non-blocking.
- If dependency issues appear, verify `pip check` first.
- If Taurus starts failing around YAML loading, re-check Taurus/PyYAML compatibility.
- For `test-advanced.yml`, sporadic TLS handshake/network errors from public endpoints may appear at low rate; treat as external instability and evaluate threshold, not as local environment breakage.

## AI-safe execution (single window)

To avoid workstation freezes when many tests are requested, run Taurus in one AI terminal window and keep single-run lock enabled (default in `run-taurus.ps1`).

- Default behavior: only one Taurus run can be active at a time.
- If another run is active, the script fails fast with an explanatory message.
- Override only when really needed: `-AllowParallel`.

## One-command runner

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"

./scripts/run-taurus.ps1 -Mode health
./scripts/run-taurus.ps1 -Mode standard
./scripts/run-taurus.ps1 -Mode jmeter-java8
./scripts/run-taurus.ps1 -Mode pipeline
```

## Custom config file

Use `-Config` to run a different Taurus scenario without editing the script.

```powershell
./scripts/run-taurus.ps1 -Mode standard -Config test-advanced.yml
./scripts/run-taurus.ps1 -Mode standard -Config test-support.yml
./scripts/run-taurus.ps1 -Mode standard -Config test-locust.yml
./scripts/run-taurus.ps1 -Mode standard -Config test-gatling.yml
./scripts/run-taurus.ps1 -Mode standard -Config test-k6.yml
./scripts/run-taurus.ps1 -Mode standard -Config test-robot.yml
./scripts/run-taurus.ps1 -Mode standard -Config test-selenium.yml
```

## VS Code tasks

| Task | Opis |
| --- | --- |
| `Taurus: Health Check` | Sprawdza środowisko |
| `Taurus: Standard API Run` | Uruchamia test-api.yml |
| `Taurus: JMeter + Java8` | Wymusza JMeter z Java 8 |
| `Taurus: Full Pipeline` | Health + Standard + JMeter |
| `Taurus: Standard Advanced Config` | Standard z test-advanced.yml |
| `Taurus: Health Advanced Config` | Health z test-advanced.yml |
| `Taurus: JMeter + Java8 Advanced Config` | JMeter z test-advanced.yml |
| `Taurus: Full Pipeline Advanced Config` | Full pipeline z test-advanced.yml |
| `Taurus: Support/Production Environment` | Standard z test-support.yml |
| `Taurus: Locust Scenario` | Standard z test-locust.yml |
| `Taurus: Selenium Scenario` | Standard z test-selenium.yml |
| `Taurus: Gatling Scenario` | Standard z test-gatling.yml |
| `Taurus: k6 Scenario` | Standard z test-k6.yml |
| `Taurus: Robot Framework Scenario` | Standard z test-robot.yml |

## VS Code debug profiles (F5)

| Profil | Opis |
| --- | --- |
| `Taurus: Uruchom test-api.yml` | Uruchamia bzt test-api.yml |
| `Taurus: Uruchom test-advanced.yml` | Uruchamia bzt test-advanced.yml |
| `Taurus: Uruchom test-locust.yml` | Uruchamia bzt test-locust.yml |
| `Taurus: Uruchom test-gatling.yml` | Uruchamia bzt test-gatling.yml |
| `Taurus: Uruchom test-k6.yml` | Uruchamia bzt test-k6.yml |
| `Taurus: Uruchom test-robot.yml` | Uruchamia bzt test-robot.yml |
| `Taurus: Uruchom test-selenium.yml` | Uruchamia bzt test-selenium.yml |
| `Taurus: Uruchom test-support.yml` | Uruchamia bzt test-support.yml |
| `Debug: diagnose-taurus` | Uruchamia diagnose-taurus.py |
| `Debug: run_pipeline` | Uruchamia run_pipeline.py |
| `Debug: test-locust (bezpośrednio)` | Locust headless, 1 user, 10s, localhost |
| `Debug: testy jednostkowe (pytest)` | pytest -v --no-header |

## Terminal fallback when output buffer is unstable

If the integrated terminal opens an alternate buffer and does not show full Taurus output, do not continue in that session.

1. Stop that terminal and start a fresh sync session.
2. Validate repository state with `git status --short`.
3. Validate run progress from the latest Taurus artifacts directory (`2026-*`) using `bzt.log`, `jmeter.log`, `kpi.jtl`, and `error.jtl`.
4. Treat `Failed to check for updates, server returned 5xx` as non-blocking.
5. Continue the pipeline only after confirming exit code 0 or equivalent artifact completion.
