Write-Host "=== RUN API + TESTS ==="

$root = "C:\Users\maxma\Desktop\1"

# Start API in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command `"& '$root\run-api.ps1'`""

# Wait for API to start
Start-Sleep -Seconds 5

# Run tests in current window
powershell -NoExit -Command "& '$root\run-test.ps1'"