# Taurus Runbook (verified on 2026-05-01)

This file captures the currently verified way to run this workspace on Windows.
Reference: <https://gettaurus.org/install/Installation/> (Windows section)

## Verified environment

- Python: `C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe` (global install)
- bzt: `1.16.50` (global, installed via pip)
- setuptools: `79.0.1` (pinned — bzt incompatible with setuptools 82.x+)
- PyYAML: `6.0.x`
- Manual JMeter available locally: `tools/apache-jmeter-5.6.3`
- Local Java 8 for compatibility runs: `tools/jdk8u482-b08`

## Windows prerequisites (one-time setup)

Required per official docs: Python 3.7+, Java, Microsoft Visual C++ (Desktop Development with C++)

```powershell
# Step 1 — upgrade pip/setuptools/wheel/Cython (wg gettaurus.org docs)
C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe -m pip install --upgrade pip setuptools wheel Cython

# Step 2 — install bzt
C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe -m pip install bzt

# Step 3 — pin setuptools (compatibility fix)
C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe -m pip install setuptools==79.0.1
```

Or use VS Code F5 profiles: "Debug: Taurus krok 1/2/3"
Or use VS Code task: "Windows: Zainstaluj wymagania systemowe (Java + VC++)"

## Fast health check

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"

C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe -V
C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe -m pip show bzt setuptools pyyaml
C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe -m pip check
C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe -h
```

## Standard API run (Public/Demo endpoints)

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"
C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe test-api.yml
```

Expected: run finishes with exit code `0`, failures `0.00%`.

## Support/Production environment run

For testing against support or production API endpoints, use `test-support.yml`.

**Before running:** update `test-support.yml` with actual support/production endpoint URLs (currently has placeholders).

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"

# Use custom config flag
./scripts/run-taurus.ps1 -Mode standard -Config test-support.yml

# Or direct bzt call
C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe test-support.yml
```

**Differences from test-api.yml:**

- Stricter concurrency (5 vs 10)
- Longer hold-for (5m vs 2m) to simulate sustained load
- Longer ramp-up (1m vs 30s)
- Lower throughput target (30 vs 50 RPS)
- Stricter pass/fail criteria (fail>5%, avg-rt>3s vs fail>10%, avg-rt>5s)

## Pass/Fail criteria (wg gettaurus.org/docs/PassFail/)

`test-api.yml` zawiera kryteria passfail:

- `fail>10% for 30s, stop as failed` — stop jeśli >10% requestów failuje przez 30s
- `avg-rt>5s for 30s, stop as failed` — stop jeśli średni czas odpowiedzi >5s przez 30s

Exit codes (wg docs):

- `0` — brak błędów
- `1` — błąd generyczny (sieć, Taurus internal)
- `2` — ręczne zatrzymanie (Ctrl+C)
- `3` — automatyczne zatrzymanie (passfail criteria)

## CLI overrides (-o switch)

```powershell
# Zmiana executora na JMeter (wg gettaurus.org/docs/CommandLine/)
bzt test-api.yml -o execution.0.executor=jmeter

# Cichy tryb (tylko błędy i ostrzeżenia)
bzt -q test-api.yml

# Tryb verbose (wszystkie logi)
bzt -v test-api.yml

# Zmiana pliku logu
bzt -l my-run.log test-api.yml
```

## Forced JMeter + Java 8 run

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"
$env:JAVA_HOME = "c:/Users/maxma/Documents/GitHub/repo-gotowe/tools/jdk8u482-b08"
$env:Path = "$env:JAVA_HOME/bin;" + $env:Path
C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe test-api.yml -o execution.0.executor=jmeter
```

Note: use `execution.0.executor=jmeter` (indexed path), not `execution.executor=jmeter`.

## Artifacts directory (wg gettaurus.org/docs/ArtifactsDir/)

Po każdym uruchomieniu Taurus tworzy katalog z timestampem, np. `2026-05-01_12-00-00.000000/`.
Zawiera:

- `bzt.log` — szczegółowy log, najlepsze źródło do troubleshootingu
- `merged.yml` / `merged.json` — konfiguracja po scaleniu wszystkich plików
- `effective.yml` / `effective.json` — konfiguracja po zastosowaniu defaults i shorthand rules

## Git hygiene used in this repo

- `tools/` is ignored in `.gitignore` (local distributions stay out of Git).
- `jmeter.log` is intentionally not tracked.
- Generated Taurus artifact folders are ignored via timestamp pattern.

## Troubleshooting notes

- Taurus update-check 5xx warnings are non-blocking.
- If dependency issues appear, verify `pip check` first.
- If Taurus starts failing around YAML loading, re-check Taurus/PyYAML compatibility.
- For `test-advanced.yml`, sporadic TLS handshake/network errors from public endpoints may appear at low rate; treat as external instability and evaluate threshold, not as local environment breakage.
- setuptools must stay at `79.0.1` — setuptools 82.x+ breaks bzt.

## One-command runner

For convenience, use `scripts/run-taurus.ps1` with one of the modes below.

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
```

## VS Code tasks

| Task | Opis |
| --- | --- |
| `Taurus: Health Check` | Sprawdza środowisko |
| `Taurus: Standard API Run` | Uruchamia test-api.yml |
| `Taurus: JMeter + Java8` | Wymusza JMeter z Java 8 |
| `Taurus: Full Pipeline` | Health + Standard + JMeter |
| `Taurus: Health Advanced Config` | Health z test-advanced.yml |
| `Taurus: Standard Advanced Config` | Standard z test-advanced.yml |
| `Windows: Zainstaluj wymagania systemowe` | Java + VC++ przez winget |

## VS Code debug profiles (F5)

| Profil | Opis |
| --- | --- |
| `Taurus: test-api.yml` | Uruchamia bzt test-api.yml |
| `Taurus: test-advanced.yml` | Uruchamia bzt test-advanced.yml |
| `Debug: Taurus krok 1` | pip install pip/setuptools/wheel/Cython |
| `Debug: Taurus krok 2` | pip install bzt |
| `Debug: Taurus krok 3` | pip install setuptools==79.0.1 |
| `Debug: Install from requirements.txt` | pip install -r requirements.txt |

## Terminal fallback when output buffer is unstable

If the integrated terminal opens an alternate buffer and does not show full Taurus output, do not continue in that session.

1. Stop that terminal and start a fresh sync session.
2. Validate repository state with `git status --short` (or Git status UI).
3. Validate run progress from the latest Taurus artifacts directory (`2026-*`) using `bzt.log`, `jmeter.log`, `kpi.jtl`, and `error.jtl`.
4. Treat `Failed to check for updates, server returned 5xx` as non-blocking.
5. Continue the pipeline only after confirming exit code 0 or equivalent artifact completion.
