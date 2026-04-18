param(
    [switch]$UseWslBootstrap,
    [switch]$SkipTests,
    [switch]$SkipReports,
    [bool]$ContinueOnReportError = $true,
    [int]$Timeout = 120
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[AUTO] $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[AUTO][OK] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "[AUTO][ERR] $Message" -ForegroundColor Red
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    & $FilePath @Arguments
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "Command failed: $FilePath $($Arguments -join ' ') (exit $exitCode)"
    }

    return $exitCode
}

function Convert-ToWslPath {
    param([string]$WindowsPath)

    $normalized = $WindowsPath -replace '\\', '/'
    if ($normalized -match '^([A-Za-z]):/(.*)$') {
        $drive = $Matches[1].ToLower()
        $rest = $Matches[2]
        return "/mnt/$drive/$rest"
    }

    throw "Cannot convert Windows path to WSL path: $WindowsPath"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$RunAllTestsScript = Join-Path $ScriptDir "run-all-tests.ps1"
$BootstrapWslScript = Join-Path $ScriptDir "bootstrap-wsl.sh"
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir ("full-auto-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

Start-Transcript -Path $LogFile -Force | Out-Null

try {
    Write-Step "Project root: $ProjectRoot"

    if ($UseWslBootstrap) {
        if (-not (Test-Path $BootstrapWslScript)) {
            throw "WSL bootstrap script not found: $BootstrapWslScript"
        }

        Write-Step "Running WSL bootstrap"
        $projectWslPath = Convert-ToWslPath -WindowsPath $ProjectRoot
        Invoke-Checked -FilePath "wsl" -Arguments @(
            "-e", "bash", "-lc",
            "cd '$projectWslPath'; VENV_DIR=\$HOME/.venv-wsl-k6 ./scripts/bootstrap-wsl.sh"
        )
        Write-Ok "WSL bootstrap completed"
    }

    if (-not $SkipTests) {
        if (-not (Test-Path $RunAllTestsScript)) {
            throw "Test orchestrator script not found: $RunAllTestsScript"
        }

        Write-Step "Running Taurus suite"
        Invoke-Checked -FilePath "powershell" -Arguments @(
            "-ExecutionPolicy", "Bypass",
            "-File", $RunAllTestsScript,
            "-Timeout", "$Timeout"
        )
        Write-Ok "Taurus suite completed"
    }

    if (-not $SkipReports) {
        $pythonPath = Join-Path $ProjectRoot ".venv/Scripts/python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }

        $reportScripts = @(
            "generate_report.py",
            "generate_html_report.py",
            "summary-report.py",
            "analyze-kpi.py"
        )

        foreach ($scriptName in $reportScripts) {
            $scriptPath = Join-Path $ProjectRoot $scriptName
            if (-not (Test-Path $scriptPath)) {
                continue
            }

            Write-Step "Running report script: $scriptName"
            $exitCode = Invoke-Checked -FilePath $pythonPath -Arguments @($scriptPath) -AllowFailure:$ContinueOnReportError
            if ($exitCode -eq 0) {
                Write-Ok "Report script finished: $scriptName"
            }
            elseif ($ContinueOnReportError) {
                Write-Fail "Report script failed, continuing: $scriptName"
            }
        }
    }

    Write-Ok "Automation pipeline completed"
    exit 0
}
catch {
    Write-Fail $_.Exception.Message
    exit 1
}
finally {
    Stop-Transcript | Out-Null
    Write-Host "[AUTO] Log saved to: $LogFile"
}
