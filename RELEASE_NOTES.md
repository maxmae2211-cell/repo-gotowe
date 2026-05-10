# Release Notes

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
