# Release Notes

## 2026-05-10 - PR #25 merge and hook/CI stabilization

### Summary

Main now includes PR #25 (guard-git hooks integration) and follow-up hardening fixes for Windows PowerShell and CI reliability.

### What was delivered

- Merged PR #25 into main, including:
  - guard-git hooks and config
  - hooks installer
  - hooks test suite (Pester)
  - hook validation workflow
- Fixed Taurus wrapper and hook installer path handling in PowerShell.
- Removed UTF-8 BOM from generated hook files to preserve executable shebang behavior.
- Fixed pre-push hook logic to block only true non-fast-forward updates on protected branches.

### Validation

- `main.yml` run #31 on main: success.
- Passing jobs:
  - Validate & Lint
  - Taurus Health Check
  - Taurus Load Test
- Local health smoke test passed: `scripts/run-taurus.ps1 -Mode health`.

## 2026-05-10 - CI and Taurus Stability Update

### Summary

This release stabilizes CI behavior and improves reliability of Taurus health-check signaling on main.

### Problem

- CI signal quality was affected by e-mail notification steps that depended on external secrets.
- Taurus wrapper health-checks could under-report failures when process exit codes were not propagated clearly.

### Root Cause

- Mail action steps in workflow introduced avoidable failure points when secrets were absent.
- Health-check command path in wrapper required explicit non-zero exit propagation.

### Fixes

- Removed e-mail notification steps from .github/workflows/full-auto.yml.
- Updated scripts/run-taurus.ps1 to propagate health-check failures via correct process exit code.
- Shipped to main through focused commits:
  - 44d4fff5
  - f1fd30fa

### Validation

All key GitHub Actions workflows for commit f1fd30fa completed with success:

- Test Automation
- Full Automation Pipeline
- CI
- Taurus Pipeline
- Taurus CI
- Publish Taurus Report
- Generate and Publish HTML Report
- Python tests
- Python application

### Impact

- Fewer false alarms in CI.
- Clearer and more trustworthy Taurus health-check behavior.
- Better release confidence on main.
