param(
    [ValidateSet('health', 'standard', 'jmeter-java8', 'pipeline')]
    [string]$Mode = 'standard',
    [string]$Config = 'test-api.yml'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$localPython = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe"
$localBzt = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe"
$python = if (Test-Path $localPython) { $localPython } else { "python" }
$bzt = if (Test-Path $localBzt) { $localBzt } else { "bzt" }
$java8 = Join-Path $repoRoot 'tools/jdk8u482-b08'
$configPath = Join-Path $repoRoot $Config

function Assert-Exists([string]$Path, [string]$Label) {
    if (-not (Test-Path $Path)) {
        throw "Nie znaleziono ${Label}: $Path"
    }
}
function Open-LatestReport {
    $reportDirs = Get-ChildItem $repoRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}\.[0-9]+$' } |
    Sort-Object LastWriteTime -Descending
    if ($reportDirs) {
        $latestDir = $reportDirs[0]
        $reportFile = Join-Path $latestDir.FullName 'report.html'
        if (Test-Path $reportFile) {
            Write-Host "Otwieram raport: $reportFile"
            Start-Process $reportFile
        }
    }
}

Assert-Exists $python 'Interpreter Python'
Assert-Exists $bzt 'Plik wykonywalny Taurusa (bzt)'
Assert-Exists $configPath 'Plik konfiguracyjny Taurusa'

switch ($Mode) {
    'health' {
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check
        & $bzt -h
    }
    'standard' {
        & $bzt $configPath
        if ($LASTEXITCODE -eq 0) {
            Open-LatestReport
        }
        else {
            Write-Host "[BLAD] Test zakonczony z bledem. Kod wyjscia: $LASTEXITCODE"
            exit $LASTEXITCODE
        }
    }
    'jmeter-java8' {
        $env:JAVA_HOME = $java8
        $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
        & $bzt $configPath -o execution.0.executor=jmeter
        if ($LASTEXITCODE -eq 0) {
            Open-LatestReport
        }
        else {
            Write-Host "[BLAD] Test JMeter zakonczony z bledem. Kod wyjscia: $LASTEXITCODE"
            exit $LASTEXITCODE
        }
    }
    'pipeline' {
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check
        & $bzt $configPath
        if ($LASTEXITCODE -eq 0) {
            $env:JAVA_HOME = $java8
            $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
            & $bzt $configPath -o execution.0.executor=jmeter
            if ($LASTEXITCODE -eq 0) {
                Open-LatestReport
            }
            else {
                Write-Host "[BLAD] Test JMeter zakonczony z bledem. Kod wyjscia: $LASTEXITCODE"
                exit $LASTEXITCODE
            }
        }
        else {
            Write-Host "[BLAD] Test API zakonczony z bledem. Kod wyjscia: $LASTEXITCODE"
            exit $LASTEXITCODE
        }
    }
}
