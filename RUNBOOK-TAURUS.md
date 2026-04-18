# Taurus Runbook (verified on 2026-04-18)

This file captures the currently verified way to run this workspace on Windows.

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

Use this when you want explicit JMeter executor with local Java 8.

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"
$env:JAVA_HOME = "c:/Users/maxma/Documents/GitHub/repo-gotowe/tools/jdk8u482-b08"
$env:Path = "$env:JAVA_HOME/bin;" + $env:Path
c:/Users/maxma/Documents/GitHub/repo-gotowe/.venv/Scripts/bzt.exe test-api.yml -o execution.0.executor=jmeter
```

Note: use `execution.0.executor=jmeter` (indexed path), not `execution.executor=jmeter`.

## Git hygiene used in this repo

- `tools/` is ignored in `.gitignore` (local distributions stay out of Git).
- `jmeter.log` is intentionally not tracked.
- Generated Taurus artifact folders are ignored via timestamp pattern.

## Troubleshooting notes

- Taurus update-check 5xx warnings are non-blocking.
- If dependency issues appear, verify `pip check` first.
- If Taurus starts failing around YAML loading, re-check Taurus/PyYAML compatibility.
- For `test-advanced.yml`, sporadic TLS handshake/network errors from public endpoints may appear at low rate; treat as external instability and evaluate threshold, not as local environment breakage.

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

## VS Code tasks (advanced config)

Use these tasks when you want to run `test-advanced.yml` from VS Code:

- `Taurus: Health Advanced Config`
- `Taurus: Standard Advanced Config`
- `Taurus: JMeter + Java8 Advanced Config`
- `Taurus: Full Pipeline Advanced Config`

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"
./scripts/run-taurus.ps1 -Mode health -Config test-advanced.yml
./scripts/run-taurus.ps1 -Mode standard -Config test-advanced.yml
./scripts/run-taurus.ps1 -Mode jmeter-java8 -Config test-advanced.yml
./scripts/run-taurus.ps1 -Mode pipeline -Config test-advanced.yml
```

## Analysis pipeline

After a Taurus run, use `run_pipeline.py` to analyze artifacts and produce a report:

```powershell
# Auto-detect latest artifact directory
python run_pipeline.py

# Point at a specific JTL file
python run_pipeline.py --jtl 2026-04-18_12-00-00.000000/kpi.jtl

# With quality gates
python run_pipeline.py --max-failures 0 --max-avg-ms 200
```

The pipeline runs three steps in sequence:
1. `analyze_kpi.py` — prints KPI summary and enforces quality gates (exit 2 on gate failure)
2. `analyze_results.py` — per-endpoint breakdown with thread statistics
3. `generate_report.py` — writes `taurus-locust-report.html`

## CI/CD pipeline (GitHub Actions)

The workflow `.github/workflows/taurus-ci.yml` runs on every push/PR to `main`:

1. **Install dependencies** — `pip install -r requirements.txt` (includes `pytest`)
2. **Unit tests** — `pytest tests/ -v` exercises `jtl_metrics.py` with a committed fixture JTL (`tests/fixtures/sample.jtl`)
3. **Analysis pipeline** — `run_pipeline.py --jtl tests/fixtures/sample.jtl` validates the full analysis chain without requiring a live Taurus run
4. **Upload artifact** — the HTML report is uploaded as a GitHub Actions artifact

> **Note:** The fixture JTL (`tests/fixtures/sample.jtl`) is a small synthetic dataset used exclusively for CI validation. It does not represent a real production load test. To analyze results from a real run, use `--jtl <path>` or rely on auto-detection (`--artifacts-pattern`).

## Java kernel timeout fix (Runme/JShell)

If Java kernel initialization fails with JShell/JDI timeout, run the helper script below and then reload the VS Code window.

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"
./scripts/fix-java-kernel.ps1 -PurgeRunmeJdkCache
# Then run: Developer: Reload Window
```

## Terminal fallback when output buffer is unstable

If the integrated terminal opens an alternate buffer and does not show full Taurus output, do not continue in that session.

1. Stop that terminal and start a fresh sync session.
2. Validate repository state with `git status --short` (or Git status UI).
3. Validate run progress from the latest Taurus artifacts directory (`2026-*`) using `bzt.log`, `jmeter.log`, `kpi.jtl`, and `error.jtl`.
4. Treat `Failed to check for updates, server returned 5xx` as non-blocking.
5. Continue the pipeline only after confirming exit code 0 or equivalent artifact completion.

