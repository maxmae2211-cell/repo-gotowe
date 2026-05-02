#Requires -Version 5.1
<#
.SYNOPSIS
    Instaluje wymagania systemowe dla Taurus na Windows (wg gettaurus.org/install/Installation/).
    Wymagane: Python 3.7+, Java, Microsoft Visual C++ Desktop Development with C++.

.NOTES
    Uruchom jako Administrator (prawy klik -> Uruchom jako administrator).
    Python 3.10 juz jest zainstalowany, wiec jest pomijany.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step { param([string]$Msg) Write-Host "`n=== $Msg ===" -ForegroundColor Cyan }
function Write-OK   { param([string]$Msg) Write-Host "[OK] $Msg" -ForegroundColor Green }
function Write-SKIP { param([string]$Msg) Write-Host "[SKIP] $Msg" -ForegroundColor Yellow }
function Write-FAIL { param([string]$Msg) Write-Host "[FAIL] $Msg" -ForegroundColor Red }

# --- Sprawdz czy winget jest dostepny ---
Write-Step "Sprawdzanie winget"
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-FAIL "winget nie jest dostepny. Zainstaluj App Installer ze sklepu Microsoft Store i sprobuj ponownie."
    exit 1
}
Write-OK "winget dostepny: $(winget --version)"

# --- Java (OpenJDK 21 LTS) ---
Write-Step "Java (OpenJDK 21 LTS) - wymagana przez Taurus/JMeter"
$javaCheck = java -version 2>&1 | Select-String "version"
if ($javaCheck) {
    Write-SKIP "Java juz zainstalowana: $javaCheck"
} else {
    Write-Host "Instalowanie Microsoft OpenJDK 21..."
    winget install --id Microsoft.OpenJDK.21 --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Java zainstalowana pomyslnie."
        Write-Host "UWAGA: Uruchom ponownie terminal/VS Code, aby Java byla widoczna w PATH." -ForegroundColor Yellow
    } else {
        Write-FAIL "Instalacja Java nie powiodla sie (kod: $LASTEXITCODE)."
    }
}

# --- Microsoft Visual C++ Build Tools (Desktop Development with C++) ---
Write-Step "Microsoft Visual C++ Build Tools - wymagane do kompilacji modulow Python (Cython, bzt)"
$vsCheck = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\VisualStudio\*\VC\Runtimes\*" -ErrorAction SilentlyContinue
if ($vsCheck) {
    Write-SKIP "Visual C++ Runtime juz zainstalowany."
} else {
    Write-Host "Instalowanie Microsoft Visual C++ Build Tools 2022..."
    winget install --id Microsoft.VisualStudio.2022.BuildTools --accept-source-agreements --accept-package-agreements `
        --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Visual C++ Build Tools zainstalowane pomyslnie."
    } else {
        Write-FAIL "Instalacja Visual C++ Build Tools nie powiodla sie (kod: $LASTEXITCODE)."
        Write-Host "Zainstaluj recznie: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Yellow
    }
}

# --- Weryfikacja po instalacji ---
Write-Step "Weryfikacja instalacji"

# Sprawdz Java
try {
    $javaVer = java -version 2>&1 | Select-String "version" | Select-Object -First 1
    if ($javaVer) {
        Write-OK "Java: $javaVer"
    } else {
        Write-FAIL "Java nie jest dostepna w PATH. Uruchom ponownie terminal."
    }
} catch {
    Write-FAIL "Java nie jest dostepna w PATH. Uruchom ponownie terminal."
}

# Sprawdz Python
try {
    $pyVer = python --version 2>&1
    Write-OK "Python: $pyVer"
} catch {
    Write-FAIL "Python nie jest dostepny w PATH."
}

# Sprawdz bzt
try {
    $bztVer = python -m bzt --version 2>&1 | Select-Object -First 1
    if ($bztVer) {
        Write-OK "bzt (Taurus): $bztVer"
    } else {
        Write-SKIP "bzt (Taurus) nie zainstalowany - uruchom krok 2 z VS Code."
    }
} catch {
    Write-SKIP "bzt (Taurus) nie zainstalowany - uruchom krok 2 z VS Code."
}

# Sprawdz cl.exe (Visual C++)
$clPath = Get-Command cl -ErrorAction SilentlyContinue
if ($clPath) {
    Write-OK "Visual C++ cl.exe: $($clPath.Source)"
} else {
    Write-SKIP "cl.exe niedostepny w biezacym PATH (normalne poza Developer Command Prompt)."
}

# --- Podsumowanie ---
Write-Step "Podsumowanie"
Write-Host ""
Write-Host "Kolejne kroki (w VS Code F5):" -ForegroundColor White
Write-Host "  1. Debug: Taurus krok 1 - pip/setuptools/wheel/Cython"
Write-Host "  2. Debug: Taurus krok 2 - install bzt"
Write-Host "  3. Debug: Taurus krok 3 - pin setuptools==79.0.1"
Write-Host ""
Write-Host "Dokumentacja: https://gettaurus.org/install/Installation/" -ForegroundColor DarkGray

Read-Host "`nNacisnij Enter aby zamknac"
