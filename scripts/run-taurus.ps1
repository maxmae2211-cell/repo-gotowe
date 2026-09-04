param(
    [ValidateSet('health', 'standard', 'jmeter-java8', 'pipeline')]
    [string]$Mode = 'health',
    [string]$Config = 'test-api.yml',
    [switch]$AllowParallel
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$runLogDir = Join-Path $repoRoot 'logs'
if (-not (Test-Path $runLogDir)) {
    New-Item -ItemType Directory -Path $runLogDir -Force | Out-Null
}
$runLogFile = Join-Path $runLogDir ("taurus-" + $Mode + "-" + (Get-Date -Format 'yyyy-MM-dd_HH-mm-ss') + ".log")

function Write-RunLog {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$timestamp] $Message"
    Write-Host $line
}

try {
    Start-Transcript -Path $runLogFile -Force -Append:$false | Out-Null
}
catch {
    Write-Warning "Nie można uruchomić transkrypcji logów: $($_.Exception.Message)"
}

# --- Skonfiguruj JAVA_HOME zanim uruchomisz Taurus ---
function Configure-JavaHome {
    if ($env:JAVA_HOME) {
        $configuredJava = Join-Path $env:JAVA_HOME 'bin\java.exe'
        if (Test-Path -LiteralPath $configuredJava -PathType Leaf) {
            $env:PATH = "$($env:JAVA_HOME)\bin;$($env:PATH)"
            Write-Host "[JAVA] Używam istniejące JAVA_HOME: $($env:JAVA_HOME)" -ForegroundColor Green
            return $true
        }

        Write-Host "[JAVA] Zmienna JAVA_HOME jest niepoprawna: $($env:JAVA_HOME). Szukam poprawnej instalacji Java..." -ForegroundColor Yellow
    }

    $repoJdk8 = Join-Path $repoRoot 'tools\jdk8u482-b08'
    if ((Test-Path $repoJdk8) -and (Test-Path (Join-Path $repoJdk8 'bin\java.exe'))) {
        $env:JAVA_HOME = $repoJdk8
        $env:PATH = "$($env:JAVA_HOME)\bin;$($env:PATH)"
        Write-Host "[JAVA] Uzywam repo JDK8: $($env:JAVA_HOME)" -ForegroundColor Green
        return $true
    }

    $javaCmd = Get-Command java -ErrorAction SilentlyContinue
    if ($javaCmd) {
        $javaExe = $javaCmd.Source
        $javaRoot = Split-Path -Parent $javaExe
        $env:JAVA_HOME = Split-Path -Parent $javaRoot
        $env:PATH = "$($env:JAVA_HOME)\bin;$($env:PATH)"
        Write-Host "[JAVA] Uzywam Java z PATH: $($env:JAVA_HOME)" -ForegroundColor Green
        return $true
    }

    $openJdkPaths = @(
        'C:\Program Files\OpenJDK\jdk-21*',
        'C:\Program Files\Microsoft\jdk-21*',
        'C:\Program Files\Java\jdk-21*',
        'C:\Program Files\Eclipse Adoptium\jdk-21*'
    )

    foreach ($pattern in $openJdkPaths) {
        $javaHome = Get-Item $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($javaHome) {
            $env:JAVA_HOME = $javaHome.FullName
            $env:PATH = "$($env:JAVA_HOME)\bin;$($env:PATH)"
            Write-Host "[JAVA] Skonfigurowano JAVA_HOME: $($javaHome.FullName)" -ForegroundColor Green
            return $true
        }
    }

    Write-Host "[JAVA] Nie znaleziono Java 21 ani Java z PATH. Taurus może nadal zadziałać, jeśli Java będzie dostępne podczas uruchomienia." -ForegroundColor Yellow
    return $false
}

Configure-JavaHome

# --- SprawdĹş i zainstaluj Git hooks przy pierwszym uruchomieniu ---
function Install-GitHooksIfNeeded {
    $hooksDir = Join-Path (Join-Path $repoRoot ".git") "hooks"
    $preCommitHook = Join-Path $hooksDir "pre-commit"
    if (-not (Test-Path $preCommitHook)) {
        Write-Host "[guard-git] Hooki Git nie sÄ… zainstalowane." -ForegroundColor Yellow
        $installer = Join-Path $repoRoot ".github" "hooks" "install-hooks.ps1"
        if (Test-Path $installer) {
            Write-Host "[guard-git] Uruchamiam instalator hookĂłw..." -ForegroundColor Cyan
            $psExe = if ($PSVersionTable.PSEdition -eq 'Core') { "pwsh" } else { "powershell" }
            & $psExe -NoProfile -ExecutionPolicy Bypass -File $installer
        }
        else {
            Write-Warning "[guard-git] Brak instalatora hookĂłw: $installer"
        }
    }
}
Install-GitHooksIfNeeded
# ---------------------------------------------------------------

# Resolve the project Taurus environment first, then PATH fallback.
$projectPython = Join-Path $repoRoot '.venv-taurus\Scripts\python.exe'
$projectBzt = Join-Path $repoRoot '.venv-taurus\Scripts\bzt.exe'

$python = $null
$bztCmd = $null

if (Test-Path -LiteralPath $projectPython -PathType Leaf) {
    $python = $projectPython
}
else {
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $python = $pythonCommand.Source
    }
}

if (Test-Path -LiteralPath $projectBzt -PathType Leaf) {
    $bztCmd = $projectBzt
}
else {
    $bztCommand = Get-Command bzt.exe -ErrorAction SilentlyContinue
    if ($bztCommand) {
        $bztCmd = $bztCommand.Source
    }
}

function Assert-Command([string]$CommandPath, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($CommandPath)) {
        throw "Nie znaleziono ${Label}. Utworz środowisko .venv-taurus albo dodaj Python do PATH."
    }

    if ($CommandPath -ne 'python.exe' -and
        -not (Test-Path -LiteralPath $CommandPath -PathType Leaf)) {
        throw "Nie znaleziono ${Label}: $CommandPath"
    }
}

function Invoke-Bzt {
    param([string[]]$ExtraArgs)

    # Ważne: stdout polecenia jest przekierowywany przez Write-Host, żeby
    # nie trafiał do strumienia zwrotnego funkcji. W przeciwnym razie
    # `$x = Invoke-Bzt ...` łączyłby cały wypisany tekst z wartością $exitCode,
    # co powodowało fałszywe niezerowe porównania mimo poprawnego zakończenia.
    if ($bztCmd) {
        $displayCommand = $bztCmd
        & $bztCmd @ExtraArgs | ForEach-Object { Write-Host $_ }
    }
    else {
        $displayCommand = "$python -m bzt"
        & $python -m bzt @ExtraArgs | ForEach-Object { Write-Host $_ }
    }

    $exitCode = $LASTEXITCODE
    Write-RunLog "[CMD] $displayCommand $($ExtraArgs -join ' ')"
    Write-RunLog "[EXIT] Kod wyjścia: $exitCode"

    return $exitCode
}

$java8 = Join-Path $repoRoot 'tools/jdk8u482-b08'
$systemJava8 = 'C:\Program Files\BellSoft\LibericaJDK-8'
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

function Use-JavaForJMeter {
    $java8Candidates = @($java8, $systemJava8)
    $java8Home = $java8Candidates |
        Where-Object { Test-Path -LiteralPath (Join-Path $_ 'bin\java.exe') } |
        Select-Object -First 1

    if ($java8Home) {
        $env:JAVA_HOME = $java8Home
        $env:Path = "$($env:JAVA_HOME)\bin;$($env:Path)"
        Write-Host "[JAVA] Używam repo JDK: $env:JAVA_HOME"
        return
    }

    $javaCommand = Get-Command java.exe -ErrorAction SilentlyContinue
    if ($javaCommand) {
        # java -version pisze na stderr; przy globalnym $ErrorActionPreference = 'Stop'
        # połączenie strumieni przez 2>&1 zamieniłoby to na wyjątek. Wyłączamy
        # eskalację błędów tylko na czas tego wywołania.
        $previousEap = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $javaVersion = & $javaCommand.Source -version 2>&1
        }
        finally {
            $ErrorActionPreference = $previousEap
        }

        $env:JAVA_HOME = Split-Path -Parent (Split-Path -Parent $javaCommand.Source)
        Write-Host "[JAVA] Używam Java z PATH: $env:JAVA_HOME"
        Write-Host ($javaVersion -join [Environment]::NewLine)
        return
    }

    throw "Nie znaleziono Java. Dodaj JDK do PATH albo umieść JDK w tools\jdk8u482-b08."
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

$scriptExitCode = 0

try {
    Assert-Command $python 'Interpreter Python'

    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        throw "Nie znaleziono pliku konfiguracyjnego Taurusa: $configPath"
    }

    Write-RunLog "[START] Tryb: $Mode, konfig: $Config, log: $runLogFile"

    switch ($Mode) {
        'health' {
            & $python -V
            if ($LASTEXITCODE -ne 0) { throw "Python nie uruchomił się poprawnie." }

            & $python -m pip show bzt setuptools pyyaml
            if ($LASTEXITCODE -ne 0) { throw "Brak wymaganych pakietów Python." }

            & $python -m pip check
            if ($LASTEXITCODE -ne 0) { throw "pip check wykrył niespójności zależności." }

            $bztExitCode = Invoke-Bzt @('-h')
            if ($bztExitCode -ne 0) {
                throw "Taurus/bzt zakończył tryb health kodem: $bztExitCode"
            }

            Write-Host '[OK] Health check zakończony pomyślnie.' -ForegroundColor Green
            break
        }

        'standard' {
            $exitCode = Invoke-Bzt @($configPath)

            if ($exitCode -eq 0) {
                Open-LatestReport
            }
            else {
                throw "Test standard zakończył się kodem: $exitCode"
            }

            break
        }

        'jmeter-java8' {
            Write-Host '[Uruchamiam] Test JMeter z Java 8...'
            Use-JavaForJMeter

            $exitCode = Invoke-Bzt @($configPath, '-o', 'execution.0.executor=jmeter')

            if ($exitCode -eq 0) {
                Write-Host '[OK] Test JMeter zakończony pomyślnie.' -ForegroundColor Green
                Open-LatestReport
            }
            else {
                throw "Test JMeter zakończył się kodem: $exitCode"
            }

            break
        }

        'pipeline' {
            Write-Host '[1/4] Health check...'

            & $python -V
            if ($LASTEXITCODE -ne 0) {
                throw 'Python nie uruchomił się poprawnie.'
            }

            & $python -m pip show bzt setuptools pyyaml
            if ($LASTEXITCODE -ne 0) {
                throw 'Brak wymaganych pakietów Python.'
            }

            & $python -m pip check
            if ($LASTEXITCODE -ne 0) {
                throw 'pip check wykrył niespójności zależności.'
            }

            $healthExitCode = Invoke-Bzt @('-h')
            if ($healthExitCode -ne 0) {
                throw "Health check Taurus zakończył się kodem: $healthExitCode"
            }

            Write-Host '[2/4] Standard API run...'
            $standardExitCode = Invoke-Bzt @($configPath)
            if ($standardExitCode -ne 0) {
                throw "Test API zakończył się kodem: $standardExitCode"
            }

            Write-Host '[3/4] JMeter + Java 8 run...'
            Use-JavaForJMeter

            $jmeterExitCode = Invoke-Bzt @(
                $configPath,
                '-o',
                'execution.0.executor=jmeter'
            )

            if ($jmeterExitCode -ne 0) {
                throw "Test JMeter zakończył się kodem: $jmeterExitCode"
            }

            Write-Host '[4/4] Generowanie raportu HTML...'
            $reportGenerator = Join-Path $repoRoot 'generate_report.py'

            if (Test-Path -LiteralPath $reportGenerator -PathType Leaf) {
                & $python $reportGenerator

                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "Generowanie raportu zakończyło się kodem: $LASTEXITCODE"
                }
                else {
                    Write-Host '[OK] Raport HTML wygenerowany pomyślnie.' -ForegroundColor Green
                }
            }
            else {
                Write-Warning "Brak generatora raportu: $reportGenerator"
            }

            Open-LatestReport
            Write-Host '[OK] Cały pipeline zakończył się pomyślnie.' -ForegroundColor Green
            break
        }
    }
}
catch {
    $scriptExitCode = 1
    $message = $_.Exception.Message
    Write-RunLog "[BLAD] $message"
    Write-Error $message
}
finally {
    if ($runMutex) {
        try { $runMutex.ReleaseMutex() | Out-Null } catch { }
        $runMutex.Dispose()
    }

    try {
        Stop-Transcript | Out-Null
    }
    catch {
    }
}

exit $scriptExitCode

