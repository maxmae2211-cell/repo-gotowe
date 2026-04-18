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
- `Taurus: Standard Advanced Config`
- `Taurus: Full Pipeline Advanced Config`

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"
./scripts/run-taurus.ps1 -Mode standard -Config test-advanced.yml
./scripts/run-taurus.ps1 -Mode pipeline -Config test-advanced.yml
```
