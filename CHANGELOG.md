# Changelog

All notable changes to this project will be documented in this file.

## 2026-05-10 (Post-merge stabilization)

### Added

- Merged guard-git hooks integration from PR #25 into main (hooks, tests, validation workflow).

### Fixed

- Fixed PowerShell path composition in Taurus wrapper and hooks installer (`Join-Path` compatibility).
- Updated hooks installer to write hook files as UTF-8 without BOM, preventing shebang execution issues.
- Stabilized guard-git script parsing and runtime behavior on Windows PowerShell.
- Corrected pre-push force-push detection to use stdin refs and non-fast-forward detection.

### Validation

- Main workflow `main.yml` run #31 completed with success on main.
- Jobs passed: Validate & Lint, Taurus Health Check, Taurus Load Test.
- Local smoke test passed: `scripts/run-taurus.ps1 -Mode health`.

## 2026-05-10

### Fixed

- Removed e-mail notification steps from GitHub Actions workflow to eliminate diagnostics and failures caused by missing mail secrets.
- Improved health-check failure propagation in Taurus PowerShell wrapper so non-zero exit codes are returned reliably.

### CI Validation

- All key workflows for commit f1fd30fa completed successfully:
  - Test Automation
  - Full Automation Pipeline
  - CI
  - Taurus Pipeline
  - Taurus CI
  - Publish Taurus Report
  - Generate and Publish HTML Report
  - Python tests
  - Python application

### Technical Scope

- Workflow changes in .github/workflows/full-auto.yml
- Wrapper error handling changes in scripts/run-taurus.ps1
- Mainline commits included:
  - 44d4fff5
  - f1fd30fa
