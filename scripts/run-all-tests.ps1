# Taurus Performance Testing - All Tests Runner
# PowerShell Script for running complete test suite

param(
    [switch]$Verbose = $false,
    [int]$Timeout = 60
)

# Color functions
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

# Get paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Info "========================================"
Write-Info "Taurus Performance Testing Suite"
Write-Info "========================================"
Write-Host "Project: $ProjectRoot"
Write-Host "Script: $($MyInvocation.MyCommand.Path)"
Write-Host ""

# Start mock API server
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

# Verify server is running
Write-Info "Verifying mock API server..."
$serverRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/get" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Success "Mock API server running on http://localhost:8080"
        $serverRunning = $true
    }
}
catch {
    Write-Error-Custom "WARNING: Could not verify mock server - continuing anyway..."
}

Write-Host ""

# Find test files
$apiTestPath = Join-Path $ProjectRoot "tests\api"
$uiTestPath = Join-Path $ProjectRoot "tests\ui"

if (-not (Test-Path $apiTestPath)) {
    Write-Error-Custom "ERROR: API tests directory not found: $apiTestPath"
    if ($serverProcess) { $serverProcess | Stop-Process -Force -ErrorAction SilentlyContinue }
    exit 1
}

# Get all test files
$apiTests = Get-ChildItem -Path $apiTestPath -Filter "*.yml" | Sort-Object Name
$uiTests = Get-ChildItem -Path $uiTestPath -Filter "*.yml" -ErrorAction SilentlyContinue | Sort-Object Name
$allTests = @() + $apiTests + $uiTests

if ($allTests.Count -eq 0) {
    Write-Error-Custom "ERROR: No test files found"
    if ($serverProcess) { $serverProcess | Stop-Process -Force }
    exit 1
}

Write-Info "Found $($allTests.Count) test files"
Write-Host ""

# Run tests
$passed = 0
$failed = 0
$results = @()

foreach ($test in $allTests) {
    $testName = $test.BaseName
    Write-Info "────────────────────────────────────────"
    Write-Info "Running: $testName"
    Write-Info "────────────────────────────────────────"
    
    try {
        $output = & bzt $test.FullName 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Success "[OK] PASSED: $testName"
            $passed += 1
            $results += @{ Name = $testName; Status = "PASSED" }
        }
        else {
            Write-Error-Custom "[FAIL] FAILED: $testName (Exit Code: $exitCode)"
            $failed += 1
            $results += @{ Name = $testName; Status = "FAILED" }
        }
    }
    catch {
        Write-Error-Custom "[ERROR] Error running $testName : $_"
        $failed += 1
        $results += @{ Name = $testName; Status = "ERROR" }
    }
    
    Write-Host ""
}

# Stop mock server
Write-Info "Stopping mock API server..."
if ($serverProcess) {
    try {
        $serverProcess | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Success "Mock API server stopped"
    }
    catch {
        Write-Host "Warning: Could not stop server process: $_"
    }
}

# Summary
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

# Print detailed results
if ($Verbose) {
    Write-Host ""
    Write-Info "Detailed Results:"
    foreach ($result in $results) {
        if ($result.Status -eq "PASSED") {
            Write-Success "  ✓ $($result.Name)"
        }
        else {
            Write-Error-Custom "  ✗ $($result.Name)"
        }
    }
}

# Exit with appropriate code
if ($failed -gt 0) {
    exit 1
}
else {
    exit 0
}


# Load Testing Script - Run All Tests
# This script executes all test scenarios defined in the tests directory

param(
    [string]$TestPath = "",
    [string]$ReportPath = "",
    [switch]$Sequential = $false
)

# Get the script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Set default paths relative to project root
if ($TestPath -eq "") {
    $TestPath = Join-Path $ProjectRoot "tests"
}
if ($ReportPath -eq "") {
    $ReportPath = Join-Path $ProjectRoot "reports"
}

# Create reports directory if it doesn't exist
if (!(Test-Path $ReportPath)) {
    New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null
    Write-Host "Created reports directory: $ReportPath"
}

# Get all test YAML files from both api and ui directories
$apiTestPath = Join-Path $TestPath "api"
$uiTestPath = Join-Path $TestPath "ui"

if (!(Test-Path $apiTestPath)) {
    Write-Host "Error: API tests directory not found: $apiTestPath"
    exit 1
}
if (!(Test-Path $uiTestPath)) {
    Write-Host "Error: UI tests directory not found: $uiTestPath"
    exit 1
}

$apiTestFiles = Get-ChildItem -Path $apiTestPath -Filter "*.yml" | Sort-Object Name
$uiTestFiles = Get-ChildItem -Path $uiTestPath -Filter "*.yml" | Sort-Object Name
$allTestFiles = $apiTestFiles + $uiTestFiles

Write-Host "Found $($allTestFiles.Count) test files to run"
Write-Host "Project root: $ProjectRoot"
Write-Host "Reports will be saved to: $ReportPath"

foreach ($file in $allTestFiles) {
    $testName = $file.BaseName
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

    Write-Host ""
    Write-Host "Running: $testName..."

    try {
        # Change to project root directory before running Taurus
        Push-Location $ProjectRoot

        # Run the test with Taurus
        $process = Start-Process -FilePath "bzt" -ArgumentList $file.FullName -NoNewWindow -Wait -PassThru

        if ($process.ExitCode -eq 0) {
            Write-Host "✓ Completed: $testName"
        }
        else {
            Write-Host "✗ Failed: $testName (Exit code: $($process.ExitCode))"
        }
    }
    catch {
        Write-Host "✗ Failed: $testName - $_"
    }
    finally {
        # Always restore the original location
        Pop-Location
    }
}

Write-Host ""
Write-Host "All tests completed. Reports saved to: $ReportPath"
# Load Testing Script - Run All Tests
# This script executes all test scenarios defined in the tests directory

param(
    [string]$TestPath = "",
    [string]$ReportPath = "",
    [switch]$Sequential = $false
)

# Get the script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Set default paths relative to project root
if ($TestPath -eq "") {
    $TestPath = Join-Path $ProjectRoot "tests"
}
if ($ReportPath -eq "") {
    $ReportPath = Join-Path $ProjectRoot "reports"
}

# Create reports directory if it doesn't exist
if (!(Test-Path $ReportPath)) {
    New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null
    Write-Host "Created reports directory: $ReportPath"
}

# Get all test YAML files from both api and ui directories
$apiTestPath = Join-Path $TestPath "api"
$uiTestPath = Join-Path $TestPath "ui"

if (!(Test-Path $apiTestPath)) {
    Write-Host "Error: API tests directory not found: $apiTestPath"
    exit 1
}
if (!(Test-Path $uiTestPath)) {
    Write-Host "Error: UI tests directory not found: $uiTestPath"
    exit 1
}

$apiTestFiles = Get-ChildItem -Path $apiTestPath -Filter "*.yml" | Sort-Object Name
$uiTestFiles = Get-ChildItem -Path $uiTestPath -Filter "*.yml" | Sort-Object Name
$allTestFiles = $apiTestFiles + $uiTestFiles

Write-Host "Found $($allTestFiles.Count) test files to run"
Write-Host "Project root: $ProjectRoot"
Write-Host "Reports will be saved to: $ReportPath"

foreach ($file in $allTestFiles) {
    $testName = $file.BaseName
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

    Write-Host ""
    Write-Host "Running: $testName..."

    try {
        # Change to project root directory before running Taurus
        Push-Location $ProjectRoot

        # Run the test with Taurus
        $process = Start-Process -FilePath "bzt" -ArgumentList $file.FullName -NoNewWindow -Wait -PassThru

        if ($process.ExitCode -eq 0) {
            Write-Host "✓ Completed: $testName"
        }
        else {
            Write-Host "✗ Failed: $testName (Exit code: $($process.ExitCode))"
        }
    }
    catch {
        Write-Host "✗ Failed: $testName - $_"
    }
    finally {
        # Always restore the original location
        Pop-Location
    }
}

Write-Host ""
Write-Host "All tests completed. Reports saved to: $ReportPath"
