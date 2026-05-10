# Changelog

All notable changes to this project will be documented in this file.

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
