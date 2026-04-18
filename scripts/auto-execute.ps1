# Automatic execution startup script for Taurus
# Runs without any user interaction

param(
    [switch]$Scheduled,
    [switch]$Silent,
    [switch]$NoSilent
)

$IsSilentMode = $true
if ($PSBoundParameters.ContainsKey('Silent')) {
    $IsSilentMode = $Silent.IsPresent
}
if ($NoSilent) {
    $IsSilentMode = $false
}

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LogsDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogsDir "auto-exec-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Create logs directory
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

# Log function
function Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Add-Content -Path $LogFile -Value $logMessage
    if (-not $IsSilentMode) {
        Write-Host $logMessage
    }
}

Log "=========================================="
Log "Automatic Test Execution Started"
Log "=========================================="
Log "Project: $ProjectRoot"
Log "Scheduled: $Scheduled"
Log "Silent Mode: $IsSilentMode"

# Start mock server
Log "Starting mock API server..."
$mockServerPath = Join-Path $ProjectRoot "scripts\mock-api-server.py"
$serverProcess = Start-Process -FilePath "python" `
    -ArgumentList $mockServerPath `
    -NoNewWindow `
    -PassThru `
    -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

# Run tests
Log "Running test suite..."
$testRunnerPath = Join-Path $ProjectRoot "scripts\run-tests.py"

try {
    $output = & python $testRunnerPath 2>&1
    $exitCode = $LASTEXITCODE
    
    Log "Test execution completed with exit code: $exitCode"
    
    # Log detailed output
    $output | ForEach-Object {
        Log $_
    }
}
catch {
    Log "ERROR: $_"
    $exitCode = 1
}

# Stop server
if ($serverProcess) {
    $serverProcess | Stop-Process -Force -ErrorAction SilentlyContinue
    Log "Mock server stopped"
}

# Summary
Log "=========================================="
if ($exitCode -eq 0) {
    Log "RESULT: ALL TESTS PASSED"
}
else {
    Log "RESULT: TESTS FAILED (Exit Code: $exitCode)"
}
Log "=========================================="

exit $exitCode
