param(
    [ValidateSet('health', 'standard', 'jmeter-java8', 'pipeline')]
    [string]$Mode = 'health',
    [string]$Config = 'test-api.yml',
    [switch]$AllowParallel
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# --- Sprawdź i zainstaluj Git hooks przy pierwszym uruchomieniu ---
function Ensure-GitHooks {
    $hooksDir = Join-Path (Join-Path $repoRoot ".git") "hooks"
    $preCommitHook = Join-Path $hooksDir "pre-commit"
    if (-not (Test-Path $preCommitHook)) {
        Write-Host "[guard-git] Hooki Git nie są zainstalowane." -ForegroundColor Yellow
        $installer = Join-Path (Join-Path (Join-Path $repoRoot ".github") "hooks") "install-hooks.ps1"
        if (Test-Path $installer) {
            Write-Host "[guard-git] Uruchamiam instalator hooków..." -ForegroundColor Cyan
            $psExe = if ($PSVersionTable.PSEdition -eq 'Core') { "pwsh" } else { "powershell" }
            & $psExe -NoProfile -ExecutionPolicy Bypass -File $installer
        }
        else {
            Write-Warning "[guard-git] Brak instalatora hooków: $installer"
        }
    }
}
Ensure-GitHooks
# ---------------------------------------------------------------

# Resolve python and bzt from PATH (CI-compatible) or local install fallback
$localPython = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe"
$localBzt = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe"

$python = if (Test-Path $localPython) { $localPython } else { "python" }
$bztCmd = if (Test-Path $localBzt) { $localBzt } else { $null }

# Wrap bzt execution: prefer bzt.exe from PATH, then python -m bzt
function Invoke-Bzt {
    param([string[]]$ExtraArgs)
    if ($bztCmd) {
        & $bztCmd @ExtraArgs
    }
    elseif (Get-Command bzt -ErrorAction SilentlyContinue) {
        & bzt @ExtraArgs
    }
    else {
        & $python -m bzt @ExtraArgs
    }
}
$java8 = Join-Path $repoRoot 'tools/jdk8u482-b08'
$configPath = Join-Path $repoRoot $Config

$runMutex = $null
if (-not $AllowParallel) {
    $createdNew = $false
    $runMutex = New-Object System.Threading.Mutex($true, 'Global\repo-gotowe-taurus-single-run', [ref]$createdNew)

    if (-not $createdNew) {
        $runMutex.Dispose()
        throw "Wykryto inne aktywne uruchomienie Taurus. Aby uniknac zawieszenia komputera, uruchamiaj testy pojedynczo w jednym oknie AI."
    }

    Write-Host '[AI-SAFE] Blokada rownoleglych testow wlaczona (single-run).'
}

function Assert-Exists([string]$Path, [string]$Label) {
    if (-not (Test-Path $Path)) {
        throw "Nie znaleziono ${Label}: $Path"
    }
}

<<<<<<< HEAD
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

try {
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
                    Write-Host '[4/4] Generuje raport HTML...'
                    & $python (Join-Path $repoRoot 'generate_report.py')
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host '[OK] Raport HTML wygenerowany pomyslnie.'
                    }
                    else {
                        Write-Host "[OSTRZEZENIE] Generowanie raportu HTML zakonczone z kodem: $LASTEXITCODE"
                    }
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
}
finally {
    if ($runMutex) {
        $runMutex.ReleaseMutex() | Out-Null
        $runMutex.Dispose()
=======
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
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            Write-Host "[BLAD] Kontrola zdrowia nie powiodla sie. Kod wyjscia: $exitCode"
            exit $exitCode
        }
        Write-Host '[OK] Kontrola zdrowia zakonczona.'
        break
    }

    'standard' {
        Write-Host '[Uruchamiam] Standardowy test API...'
        Invoke-Bzt @($configPath)
        $exitCode = $LASTEXITCODE
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
        Invoke-Bzt @($configPath, "-o", "execution.0.executor=jmeter")
        $exitCode = $LASTEXITCODE
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
        Invoke-Bzt @("-h") | Out-Null
        $healthExitCode = $LASTEXITCODE
        if ($healthExitCode -ne 0) {
            Write-Host "[BLAD] Kontrola zdrowia nie powiodla sie. Kod wyjscia: $healthExitCode"
            exit $healthExitCode
        }
        Write-Host '[1/3] Kontrola zdrowia zakonczona.'

        Write-Host '[2/3] Standardowy test API...'
        Invoke-Bzt @($configPath)
        $exitCode = $LASTEXITCODE
        if ($exitCode -eq 0) {
            Write-Host '[2/3] Test API zakonczony pomyslnie.'
            Write-Host '[3/3] Test JMeter + Java8...'
            Assert-Exists $java8 'Katalog Java 8'
            $env:JAVA_HOME = $java8
            $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
            Invoke-Bzt @($configPath, "-o", "execution.0.executor=jmeter")
            $exitCode2 = $LASTEXITCODE
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
>>>>>>> main
    }
}
