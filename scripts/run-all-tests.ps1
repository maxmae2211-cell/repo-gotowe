param(
    [switch]$Verbose,
    [int]$Timeout = 60
)

function Write-Success { param([string]$Message) Write-Host $Message -ForegroundColor Green }
function Write-Error-Custom { param([string]$Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host $Message -ForegroundColor Cyan }

function Invoke-FullSuite {

    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ProjectRoot = Split-Path -Parent $ScriptDir

    $PythonPath = Join-Path $ProjectRoot ".venv/Scripts/python.exe"
    if (-not (Test-Path $PythonPath)) {
        $PythonPath = Join-Path $ProjectRoot ".venv-taurus/Scripts/python.exe"
    }
    if (-not (Test-Path $PythonPath)) {
        # Fallback do systemowego Pythona
        $PythonPath = (Get-Command python -ErrorAction SilentlyContinue)?.Source
        if (-not $PythonPath) {
            Write-Error-Custom "ERROR: Python not found (szukano .venv, .venv-taurus, PATH)"
            exit 1
        }
        Write-Info "Używam systemowego Pythona: $PythonPath"
    }

    Write-Info "========================================"
    Write-Info "Taurus Performance Testing Suite"
    Write-Info "========================================"
    Write-Host "Project: $ProjectRoot"
    Write-Host ""

    Write-Info "Starting mock API server..."

    $mockServerPath = Join-Path $ScriptDir "mock-api-server.py"
    $serverLog = Join-Path $ScriptDir "mock-server.log"

    if (-not (Test-Path $mockServerPath)) {
        Write-Error-Custom "ERROR: mock-api-server.py not found at $mockServerPath"
        exit 1
    }

    $serverProcess = Start-Process -FilePath $PythonPath `
        -ArgumentList $mockServerPath `
        -RedirectStandardOutput $serverLog `
        -RedirectStandardError $serverLog `
        -PassThru -WindowStyle Hidden

    Start-Sleep -Seconds 2

    if ($serverProcess.HasExited) {
        Write-Error-Custom "ERROR: Mock API server crashed immediately. Check $serverLog"
        exit 1
    }

    Write-Info "Verifying mock API server..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/get" -TimeoutSec 2 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Success "Mock API server running on http://localhost:8000"
        }
    }
    catch {
        Write-Error-Custom "WARNING: Could not verify mock server - continuing anyway..."
    }

    Write-Host ""

    $apiTestPath = Join-Path $ProjectRoot "tests/api"
    $uiTestPath = Join-Path $ProjectRoot "tests/ui"

    if (-not (Test-Path $apiTestPath)) {
        Write-Error-Custom "ERROR: API tests directory not found: $apiTestPath"
        $serverProcess | Stop-Process -Force
        exit 1
    }

    $apiTests = Get-ChildItem $apiTestPath -Filter "*.yml" | Sort-Object Name
    $uiTests = Get-ChildItem $uiTestPath -Filter "*.yml" -ErrorAction SilentlyContinue | Sort-Object Name

    $allTests = @() + $apiTests + $uiTests

    if ($allTests.Count -eq 0) {
        Write-Error-Custom "ERROR: No test files found"
        $serverProcess | Stop-Process -Force
        exit 1
    }

    Write-Info "Found $($allTests.Count) test files"
    Write-Host ""

    $passed = 0
    $failed = 0
    $results = @()

    foreach ($test in $allTests) {

        $testName = $test.BaseName
        Write-Info "----------------------------------------"
        Write-Info "Running: $testName"
        Write-Info "----------------------------------------"

        $testLog = Join-Path $ScriptDir "bzt-output-$testName.log"

        $process = Start-Process -FilePath $PythonPath `
            -ArgumentList "-m", "bzt", $test.FullName `
            -NoNewWindow -PassThru `
            -RedirectStandardOutput $testLog `
            -RedirectStandardError $testLog

        $finished = $process.WaitForExit($Timeout * 1000)

        if (-not $finished) {
            Write-Error-Custom "[TIMEOUT] FAILED: $testName"
            $process | Stop-Process -Force
            $failed++
            $results += @{ Name = $testName; Status = "TIMEOUT" }
            continue
        }

        $exitCode = $process.ExitCode

        if ($exitCode -eq 0) {
            Write-Success "[OK] PASSED: $testName"
            $passed++
            $results += @{ Name = $testName; Status = "PASSED" }
        }
        else {
            Write-Error-Custom "[FAIL] FAILED: $testName (Exit Code: $exitCode)"
            if ($Verbose) {
                Write-Host (Get-Content $testLog -Raw)
            }
            $failed++
            $results += @{ Name = $testName; Status = "FAILED" }
        }

        Write-Host ""
    }

    Write-Info "Stopping mock API server..."
    try {
        $serverProcess | Stop-Process -Force
        Write-Success "Mock API server stopped"
    }
    catch {
        Write-Error-Custom "Warning: Could not stop server process: $_"
    }

    Write-Host ""
    Write-Info "========================================"
    Write-Info "Test Summary"
    Write-Info "========================================"
    Write-Host "Total Tests: $($allTests.Count)"
    Write-Success "Passed: $passed"

    if ($failed -gt 0) {
        Write-Error-Custom "Failed: $failed"
    }
    else {
        Write-Success "Failed: $failed"
    }

    Write-Info "========================================"

    if ($Verbose) {
        Write-Host ""
        Write-Info "Detailed Results:"
        foreach ($result in $results) {
            if ($result.Status -eq "PASSED") {
                Write-Success "  OK  $($result.Name)"
            }
            else {
                Write-Error-Custom "  ERR $($result.Name)"
            }
        }
    }

    if ($failed -gt 0) { exit 1 }
    exit 0
}

Invoke-FullSuite