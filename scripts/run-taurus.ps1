param(
    [ValidateSet('health', 'standard', 'jmeter-java8', 'pipeline')]
    $ErrorActionPreference = 'Stop'
    $repoRoot = Split-Path -Parent $PSScriptRoot
    Set-Location $repoRoot

    $localPython = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe"
    $localBzt = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe"
    $python = if (Test-Path $localPython) { $localPython } else { "python" }
    $bzt = if (Test-Path $localBzt) { $localBzt } else { "bzt" }
    >>>>>>> qq
    $python = if (Test-Path $localPython) { $localPython } else { "python" }
    $bzt = if (Test-Path $localBzt) { $localBzt } else { "bzt" }
    >>>>>>> qq
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

    Assert-Exists $configPath 'Plik konfiguracyjny Taurusa'

    switch ($Mode) {
        'health' {
            & $python -V
            & $python -m pip show bzt setuptools pyyaml
            & $python -m pip check
            <<<<<<< HEAD
            Invoke-Bzt @("-h") | Out-Null
            $exitCode = $LASTEXITCODE
            if ($exitCode -ne 0) {
                Write-Host "[BLAD] Kontrola zdrowia nie powiodla sie. Kod wyjscia: $exitCode"
                exit $exitCode
            }
            Write-Host '[OK] Kontrola zdrowia zakonczona.'
            break
            =======
            & $bzt -h
            >>>>>>> qq
        }
        'standard' {
            <<<<<<< HEAD
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
                =======
                & $bzt $configPath
                if ($LASTEXITCODE -eq 0) {
                    Open-LatestReport
                }
                else {
                    Write-Host "[BLAD] Test zakonczony z bledem. Kod wyjscia: $LASTEXITCODE"
                    exit $LASTEXITCODE
                    >>>>>>> qq
                }
            }
            'jmeter-java8' {
                $env:JAVA_HOME = $java8
                $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
                <<<<<<< HEAD
                Invoke-Bzt @($configPath, "-o", "execution.0.executor=jmeter")
                $exitCode = $LASTEXITCODE
                if ($exitCode -eq 0) {
                    Write-Host '[OK] Test JMeter zakonczony pomyslnie.'
                    Open-LatestReport
                }
                else {
                    Write-Host "[BLAD] Test JMeter zakonczony z bledem. Kod wyjscia: $exitCode"
                    exit $exitCode
                    =======
                    & $bzt $configPath -o execution.0.executor=jmeter
                    if ($LASTEXITCODE -eq 0) {
                        Open-LatestReport
                    }
                    else {
                        Write-Host "[BLAD] Test JMeter zakonczony z bledem. Kod wyjscia: $LASTEXITCODE"
                        exit $LASTEXITCODE
                        >>>>>>> qq
                    }
                }
                'pipeline' {
                    & $python -V
                    & $python -m pip show bzt setuptools pyyaml
                    & $python -m pip check
                    <<<<<<< HEAD
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
                        =======
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
                            >>>>>>> qq
                        }
                    }
                }
