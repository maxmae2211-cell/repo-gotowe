# Taurus Runbook (verified on 2026-05-02)

This file captures the currently verified way to run this workspace on Windows.

## Latest verified pipeline results (2026-05-02)

- Health check: ✅ PASS
- Standard API run: ✅ PASS (6413 samples, 0.00% failures, duration 3:22) → Artifacts: `2026-05-02_22-06-46.903037`
- JMeter + Java8 run: ✅ PASS (6648 samples, 0.00% failures, duration 2:56) → Artifacts: `2026-05-02_22-29-26.456735`
- Full pipeline: ✅ Ready to run (all stages verified individually)

**Note**: Local JDK8 (`tools/jdk8u482-b08`) is incomplete (missing `jre/lib/amd64/jvm.cfg`). Current setup uses system Java 8 (1.8.0_491) from PATH. Scripts updated in `run-taurus.ps1` to avoid JAVA_HOME override.
 
 Health check: ✅ PASS
 Standard API run: ✅ PASS (6565 samples, 0.00% failures, duration 3:04) → Artifacts: `2026-05-02_22-36-07.933700`
 JMeter + Java8 run: ✅ PASS (6579 samples, 0.00% failures, duration 3:12) → Artifacts: `2026-05-02_22-40-01.825186`
 Full pipeline (all stages together): ✅ PASS (verified 2026-05-02 22:36-22:43)

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

Use this when you want explicit JMeter executor. Uses system Java 8 from PATH (verified: 1.8.0_491).

```powershell
Set-Location "c:/Users/maxma/Documents/GitHub/repo-gotowe"
c:/Users/maxma/Documents/GitHub/repo-gotowe/.venv/Scripts/bzt.exe test-api.yml -o execution.0.executor=jmeter
```

**Note**: The local JDK8 at `tools/jdk8u482-b08` is incomplete (missing `jre/lib/amd64/jvm.cfg`) and cannot be used. Script now relies on system Java 8 instead. Use `execution.0.executor=jmeter` (indexed path), not `execution.executor=jmeter`.

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
