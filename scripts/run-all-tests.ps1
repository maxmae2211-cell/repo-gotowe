param(
    [switch]$Verbose = $false,
    [int]$Timeout = 60
)

# ============================
# Helper Functions
# ============================

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

# ============================
# Main Test Runner Function
# ============================

function Invoke-FullSuite {

    # Paths
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ProjectRoot = Split-Path -Parent $ScriptDir

    Write-Info "========================================"
    Write-Info "Taurus Performance Testing Suite"
    Write-Info "========================================"
    Write-Host "Project: $ProjectRoot"
    Write-Host "Script: $($MyInvocation.MyCommand.Path)"
    Write-Host ""

    # ----------------------------
    # Start mock API server
    # ----------------------------
    Write-Info "Starting mock API server..."
    $mockServerPath = Join-Path $ScriptDir "mock-api-server.py"

    if (-not (Test-Path $mockServerPath)) {
        Write-Error-Custom "ERROR: mock-api-server.py not found at $mockServerPath"
        exit 1
    }

    $serverProcess = Start-Process -FilePath "python" `
        -ArgumentList $mockServerPath `
        -NoNewWindow `
        -PassThru `
        -ErrorAction SilentlyContinue

    if ($null -eq $serverProcess) {
        Write-Error-Custom "ERROR: Failed to start mock API server"
        exit 1
    }

    Start-Sleep -Seconds 2

    # Verify server
    Write-Info "Verifying mock API server..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/get" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Success "Mock API server running on http://localhost:8080"
        }
    }
    catch {
        Write-Error-Custom "WARNING: Could not verify mock server - continuing anyway..."
    }

    Write-Host ""

    # ----------------------------
    # Find test files
    # ----------------------------
    $apiTestPath = Join-Path $ProjectRoot "tests/api"
    $uiTestPath = Join-Path $ProjectRoot "tests/ui"

    if (-not (Test-Path $apiTestPath)) {
        Write-Error-Custom "ERROR: API tests directory not found: $apiTestPath"
        $serverProcess | Stop-Process -Force
        exit 1
    }

    $apiTests = Get-ChildItem -Path $apiTestPath -Filter "*.yml" | Sort-Object Name
    $uiTests = Get-ChildItem -Path $uiTestPath -Filter "*.yml" -ErrorAction SilentlyContinue | Sort-Object Name
    $allTests = @() + $apiTests + $uiTests

    if ($allTests.Count -eq 0) {
        Write-Error-Custom "ERROR: No test files found"
        $serverProcess | Stop-Process -Force
        exit 1
    }

    Write-Info "Found $($allTests.Count) test files"
    Write-Host ""

    # ----------------------------
    # Run tests
    # ----------------------------
    $passed = 0
    $failed = 0
    $results = @()

    foreach ($test in $allTests) {
        $testName = $test.BaseName
        Write-Info "----------------------------------------"
        Write-Info "Running: $testName"
        Write-Info "----------------------------------------"

        try {
            $output = & bzt $test.FullName 2>&1
            $exitCode = $LASTEXITCODE

            if ($exitCode -eq 0) {
                Write-Success "[OK] PASSED: $testName"
                $passed++
                $results += @{ Name = $testName; Status = "PASSED" }
            }
            else {
                Write-Error-Custom "[FAIL] FAILED: $testName (Exit Code: $exitCode)"
                if ($Verbose) {
                    Write-Host "Output: $output"
                }
                $failed++
                $results += @{ Name = $testName; Status = "FAILED" }
            }
        }
        catch {
            Write-Error-Custom "[ERROR] Error running $testName : $_"
            $failed++
            $results += @{ Name = $testName; Status = "ERROR" }
        }

        Write-Host ""
    }

    # ----------------------------
    # Stop mock server
    # ----------------------------
    Write-Info "Stopping mock API server..."
    try {
        $serverProcess | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Success "Mock API server stopped"
    }
    catch {
        Write-Error-Custom "Warning: Could not stop server process: $_"
    }

    # ----------------------------
    # Summary
    # ----------------------------
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

# ============================
# Run the suite
# ============================

Invoke-FullSuite