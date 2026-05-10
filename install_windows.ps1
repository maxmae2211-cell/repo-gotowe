# =============================================================
#  Instalator projektu repo-gotowe na Windows
#  Uruchomienie: prawy klik -> "Uruchom jako Administrator"
#  lub: powershell -ExecutionPolicy Bypass -File install_windows.ps1
# =============================================================

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  repo-gotowe - Instalator Windows" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Sprawdź winget ─────────────────────────────────────────
function Test-Command($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

# Jeśli winget nie jest w PATH, spróbuj znaleźć go przez AppxPackage
if (-not (Test-Command "winget")) {
    $appInstaller = Get-AppxPackage -Name Microsoft.DesktopAppInstaller -ErrorAction SilentlyContinue
    if ($appInstaller) {
        $wingetExe = Join-Path $appInstaller.InstallLocation "winget.exe"
        if (Test-Path $wingetExe) {
            Set-Alias -Name winget -Value $wingetExe -Scope Global
            Write-Host "[INFO] winget znaleziony w: $wingetExe" -ForegroundColor Gray
        } else {
            Write-Host "[BLAD] winget nie jest dostepny." -ForegroundColor Red
            Write-Host "Zaktualizuj Windows 10/11 lub zainstaluj App Installer ze sklepu Microsoft." -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "[BLAD] winget nie jest dostepny." -ForegroundColor Red
        Write-Host "Zaktualizuj Windows 10/11 lub zainstaluj App Installer ze sklepu Microsoft." -ForegroundColor Yellow
        exit 1
    }
}

# ── 2. Python 3.11 ───────────────────────────────────────────
Write-Host "[1/5] Sprawdzam Python..." -ForegroundColor Yellow
if (-not (Test-Path "C:\Program Files\Python311\python.exe") -and -not (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe")) {
    Write-Host "     Instaluję Python 3.11..." -ForegroundColor Gray
    winget install --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
}
$python311 = @(
    "C:\Program Files\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $python311) { throw "Nie znaleziono Python 3.11 po instalacji." }
Write-Host "     OK: $(& $python311 --version)" -ForegroundColor Green

# ── 3. Java 21 (wymagany przez JMeter/Taurus) ────────────────
Write-Host "[2/5] Sprawdzam Java..." -ForegroundColor Yellow
if (-not (Test-Command "java")) {
    Write-Host "     Instaluję OpenJDK 21..." -ForegroundColor Gray
    winget install --id Microsoft.OpenJDK.21 --silent --accept-package-agreements --accept-source-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
} else {
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $javaVer = java -version 2>&1 | Select-Object -First 1
    $ErrorActionPreference = $prevEAP
    Write-Host "     OK: $javaVer" -ForegroundColor Green
}

# ── 4. Git ───────────────────────────────────────────────────
Write-Host "[3/5] Sprawdzam Git..." -ForegroundColor Yellow
if (-not (Test-Command "git")) {
    Write-Host "     Instaluję Git..." -ForegroundColor Gray
    winget install --id Git.Git --silent --accept-package-agreements --accept-source-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
} else {
    Write-Host "     OK: $(git --version)" -ForegroundColor Green
}

# ── 5. Pip packages ──────────────────────────────────────────
Write-Host "[4/5] Instaluję pakiety Python..." -ForegroundColor Yellow
Set-Location $projectDir

$venvDir = Join-Path $projectDir '.venv-taurus'
if (-not (Test-Path (Join-Path $venvDir 'Scripts\python.exe'))) {
    Write-Host "     Tworzę środowisko .venv-taurus..." -ForegroundColor Gray
    & $python311 -m venv $venvDir
}
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
& $venvPython -m pip install --upgrade pip setuptools==79.0.1 wheel --quiet

$packages = @(
    "bzt>=1.16.0",
    "python-dotenv>=1.0.0",
    "requests>=2.32.0",
    "pyyaml>=6.0",
    "pytest",
    "httpx"
)

foreach ($pkg in $packages) {
    Write-Host "     pip install $pkg" -ForegroundColor Gray
    & $venvPython -m pip install $pkg --quiet
}

# ── 6. Konfiguracja .env ─────────────────────────────────────
Write-Host "[5/5] Konfiguracja..." -ForegroundColor Yellow
$envPath = Join-Path $projectDir ".env"
$envExample = Join-Path $projectDir ".env.example"
if (-not (Test-Path $envPath)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envPath
        Write-Host "     Utworzono .env z szablonu - uzupelnij klucze API!" -ForegroundColor Yellow
    }
}

# ── Weryfikacja ───────────────────────────────────────────────
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  Weryfikacja instalacji" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$ok = $true

try { $v = & $venvPython --version 2>&1; Write-Host "  Python:  $v" -ForegroundColor Green } catch { Write-Host "  Python:  BLAD" -ForegroundColor Red; $ok = $false }
$prevEAP2 = $ErrorActionPreference; $ErrorActionPreference = "Continue"
$javaCheck = java -version 2>&1 | Select-Object -First 1
$ErrorActionPreference = $prevEAP2
if ($javaCheck) { Write-Host "  Java:    $javaCheck" -ForegroundColor Green } else { Write-Host "  Java:    BLAD (Taurus/JMeter nie bedzie dzialac)" -ForegroundColor Yellow }
try { $v = & $venvPython -c "import bzt; print(bzt.VERSION)" 2>&1; Write-Host "  Taurus:  $v" -ForegroundColor Green } catch { Write-Host "  Taurus:  BLAD" -ForegroundColor Red; $ok = $false }

Write-Host ""
if ($ok) {
    Write-Host "  Instalacja zakonczona pomyslnie!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Jak uruchomic:" -ForegroundColor Cyan
    Write-Host "    Taurus testy:    bzt test-api.yml" -ForegroundColor White
    Write-Host "    Pytest:          python -m pytest" -ForegroundColor White
} else {
    Write-Host "  Niektore komponenty nie zostaly zainstalowane!" -ForegroundColor Red
}

Write-Host ""
Write-Host "Instalator zakonczyl dzialanie."
