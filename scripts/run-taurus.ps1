param(
    [ValidateSet('health', 'standard', 'jmeter-java8', 'pipeline')]
    [string]$Mode = 'health',
    [string]$Config = 'test-api.yml'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = Join-Path $repoRoot '.venv/Scripts/python.exe'
$bzt = Join-Path $repoRoot '.venv/Scripts/bzt.exe'
$java8 = Join-Path $repoRoot 'tools/jdk8u482-b08'
$configPath = Join-Path $repoRoot $Config

function Assert-Exists([string]$Path, [string]$Label) {
    if (-not (Test-Path $Path)) {
        throw "Nie znaleziono ${Label}: $Path"
    }
}

function Use-JavaForJMeter {
    $localJavaBin = Join-Path $java8 'bin\java.exe'
    $localJvmCfg = Join-Path $java8 'jre\lib\amd64\jvm.cfg'

    if ((Test-Path $localJavaBin) -and (Test-Path $localJvmCfg)) {
        $env:JAVA_HOME = $java8
        $env:Path = "$($env:JAVA_HOME)\bin;" + $env:Path
        Write-Host "[JAVA] Uzywam lokalnego Java 8: $localJavaBin"
        return
    }

    $javaVersionOutput = & cmd /c "java -version 2>&1"
    if ($LASTEXITCODE -ne 0) {
        throw "Nie znaleziono dzialajacego Java runtime. Lokalny JDK8 jest niekompletny, a systemowe 'java' nie jest dostepne w PATH."
    }

    Remove-Item Env:JAVA_HOME -ErrorAction SilentlyContinue
    Write-Host "[JAVA] Lokalny JDK8 jest niekompletny, uzywam systemowego Java z PATH."
    $javaVersionOutput | ForEach-Object { Write-Host $_ }
}

function Open-LatestReport {
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
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check
        & $bzt -h
        break
    }

    'standard' {
        & $bzt $configPath
        if ($LASTEXITCODE -eq 0) {
            Open-LatestReport
        }
        break
    }

    'jmeter-java8' {
        Write-Host '[Uruchamiam] Test JMeter z Java 8...'
        Use-JavaForJMeter
        & $bzt $configPath -o execution.0.executor=jmeter
        if ($LASTEXITCODE -eq 0) {
            Write-Host '[OK] Test JMeter zakonczony pomyslnie.'
            Open-LatestReport
        }
        break
    }

    'pipeline' {
        Write-Host '[1/3] Health check...'
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check

        Write-Host '[2/3] Standard API run...'
        & $bzt $configPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host '[2/3] Test API zakonczony pomyslnie.'
            Write-Host '[3/3] JMeter + Java8 run...'
            Use-JavaForJMeter
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
