param(
    [ValidateSet('health', 'standard', 'jmeter-java8', 'pipeline')]
    [string]$Mode = 'health',
    [string]$Config = 'test-api.yml'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# Taurus installed globally in Python310 (see gettaurus.org/install/Installation/ - Windows)
$python = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe"
$bzt = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe"
$java8 = Join-Path $repoRoot 'tools/jdk8u482-b08'
$configPath = Join-Path $repoRoot $Config

function Assert-Exists([string]$Path, [string]$Label) {
    if (-not (Test-Path $Path)) {
        throw "Nie znaleziono $Label: $Path"
    }
}

function Open-LatestReport {
    # Znajdź najnowszy katalog z wynikami Taurusa (format: YYYY-MM-DD_HH-MM-SS.xxxxxx)
    $reportDirs = Get-ChildItem $repoRoot -Directory -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.\d+$' } |
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
        Write-Host '[Kontrola zdrowia] Sprawdzam srodowisko Taurusa...'
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check
        & $bzt -h
        Write-Host '[OK] Kontrola zdrowia zakonczona.'
        break
    }

    'standard' {
        Write-Host '[Uruchamiam] Standardowy test API...'
        & $bzt $configPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host '[OK] Test zakonczony pomyslnie.'
            Open-LatestReport
        }
        else {
            Write-Host "[BLAD] Test zakonczony z bledem. Kod wyjscia: $LASTEXITCODE"
        }
        break
    }

    'jmeter-java8' {
        Write-Host '[Uruchamiam] Test JMeter z Java 8...'
        Assert-Exists $java8 'Katalog Java 8'
        $env:JAVA_HOME = $java8
        $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
        & $bzt $configPath -o execution.0.executor=jmeter
        if ($LASTEXITCODE -eq 0) {
            Write-Host '[OK] Test JMeter zakonczony pomyslnie.'
            Open-LatestReport
        }
        else {
            Write-Host "[BLAD] Test JMeter zakonczony z bledem. Kod wyjscia: $LASTEXITCODE"
        }
        break
    }

    'pipeline' {
        Write-Host '[1/3] Kontrola zdrowia srodowiska...'
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check
        Write-Host '[1/3] Kontrola zdrowia zakonczona.'

        Write-Host '[2/3] Standardowy test API...'
        & $bzt $configPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host '[2/3] Test API zakonczony pomyslnie.'
            Write-Host '[3/3] Test JMeter + Java8...'
            Assert-Exists $java8 'Katalog Java 8'
            $env:JAVA_HOME = $java8
            $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
            & $bzt $configPath -o execution.0.executor=jmeter
            if ($LASTEXITCODE -eq 0) {
                Write-Host '[3/3] Test JMeter zakonczony pomyslnie. Caly potok wykonany!'
                Open-LatestReport
            }
            else {
                Write-Host "[BLAD] Test JMeter zakonczony z bledem. Kod wyjscia: $LASTEXITCODE"
            }
        }
        else {
            Write-Host "[BLAD] Test API zakonczony z bledem. Kod wyjscia: $LASTEXITCODE. Przerywam potok."
        }
        break
    }
}
