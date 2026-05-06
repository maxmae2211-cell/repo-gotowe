param(
    [int]$Port = 8000
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

$VenvPath = Join-Path $ProjectRoot ".venv-taurus\Scripts\Activate.ps1"
if (-not (Test-Path $VenvPath)) {
    $VenvPath = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
}

if (Test-Path $VenvPath) {
    . $VenvPath
}

Set-Location ".\api"

uvicorn main:app --reload --port $Port