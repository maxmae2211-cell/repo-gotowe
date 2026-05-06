Write-Host "=== RUN API + TESTS ==="

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start API in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command `"& '$root\run-api.ps1'`""

# Wait for API to start
Start-Sleep -Seconds 5

# Run tests in current window
powershell -NoExit -Command "& '$root\run-test.ps1'"