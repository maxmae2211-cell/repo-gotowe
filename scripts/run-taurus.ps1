param(
    [ValidateSet('health', 'standard', 'jmeter-java8', 'pipeline')]
    [string]$Mode = 'health',
    [string]$Config = 'test-api.yml'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# Resolve python and bzt from PATH (CI-compatible) or local install fallback
$localPython = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe"
$localBzt    = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe"

$python = if (Test-Path $localPython) { $localPython } else { "python" }
$bztCmd = if (Test-Path $localBzt) { $localBzt } else { $null }

# Wrap bzt execution: prefer bzt.exe from PATH, then python -m bzt
function Invoke-Bzt {
    param([string[]]$ExtraArgs)
    if ($bztCmd) {
        & $bztCmd @ExtraArgs
    } elseif (Get-Command bzt -ErrorAction SilentlyContinue) {
        & bzt @ExtraArgs
    } else {
        & $python -m bzt @ExtraArgs
    }
    return $LASTEXITCODE
}

$java8 = Join-Path $repoRoot 'tools/jdk8u482-b08'
$configPath = Join-Path $repoRoot $Config

function Assert-Exists([string]$Path, [string]$Label) {
    if (-not (Test-Path $Path)) {
        throw "Nie znaleziono ${Label}: $Path"
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

Assert-Exists $configPath 'Plik konfiguracyjny Taurusa'

switch ($Mode) {
    'health' {
        Write-Host '[Kontrola zdrowia] Sprawdzam srodowisko Taurusa...'
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check
        Invoke-Bzt @("-h") | Out-Null
        Write-Host '[OK] Kontrola zdrowia zakonczona.'
        break
    }

    'standard' {
        Write-Host '[Uruchamiam] Standardowy test API...'
        $exitCode = Invoke-Bzt @($configPath)
        if ($exitCode -eq 0) {
            Write-Host '[OK] Test zakonczony pomyslnie.'
            Open-LatestReport
        }
        else {
            Write-Host "[BLAD] Test zakonczony z bledem. Kod wyjscia: $exitCode"
            exit $exitCode
        }
        break
    }

    'jmeter-java8' {
        Write-Host '[Uruchamiam] Test JMeter z Java 8...'
        Assert-Exists $java8 'Katalog Java 8'
        $env:JAVA_HOME = $java8
        $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
        $exitCode = Invoke-Bzt @($configPath, "-o", "execution.0.executor=jmeter")
        if ($exitCode -eq 0) {
            Write-Host '[OK] Test JMeter zakonczony pomyslnie.'
            Open-LatestReport
        }
        else {
            Write-Host "[BLAD] Test JMeter zakonczony z bledem. Kod wyjscia: $exitCode"
            exit $exitCode
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
        $exitCode = Invoke-Bzt @($configPath)
        if ($exitCode -eq 0) {
            Write-Host '[2/3] Test API zakonczony pomyslnie.'
            Write-Host '[3/3] Test JMeter + Java8...'
            Assert-Exists $java8 'Katalog Java 8'
            $env:JAVA_HOME = $java8
            $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
            $exitCode2 = Invoke-Bzt @($configPath, "-o", "execution.0.executor=jmeter")
            if ($exitCode2 -eq 0) {
                Write-Host '[3/3] Test JMeter zakonczony pomyslnie. Caly potok wykonany!'
                Open-LatestReport
            }
            else {
                Write-Host "[BLAD] Test JMeter zakonczony z bledem. Kod wyjscia: $exitCode2"
                exit $exitCode2
            }
        }
        else {
            Write-Host "[BLAD] Test API zakonczony z bledem. Kod wyjscia: $exitCode. Przerywam potok."
            exit $exitCode
        }
        break
    }
}
