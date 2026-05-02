#!/usr/bin/env pwsh
# guard-git.ps1 — blokuje wrażliwe pliki w staged (pre-commit)
#                 oraz blokuje force-push do chronionych gałęzi (pre-push)
# Zainstaluj przez: .github/hooks/install-hooks.ps1

param(
    [ValidateSet("pre-commit", "pre-push")]
    [string]$HookType = "pre-commit"
)

$ErrorActionPreference = "Stop"
$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { $repoRoot = (Get-Location).Path }

$configPath = Join-Path $PSScriptRoot ".." "guard-git.json"
if (-not (Test-Path $configPath)) {
    $configPath = Join-Path $repoRoot ".github" "hooks" "guard-git.json"
}

if (-not (Test-Path $configPath)) {
    Write-Warning "guard-git: brak pliku konfiguracyjnego $configPath — hook pominięty."
    exit 0
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$warnOnly   = [bool]$config.warn_only
$logBlocked = [bool]$config.log_blocked

function Write-Blocked([string]$Message) {
    Write-Host "guard-git [ZABLOKOWANO]: $Message" -ForegroundColor Red
    if ($logBlocked) {
        $logFile = Join-Path $repoRoot ".git" "guard-git.log"
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] BLOCKED ($HookType): $Message" |
            Add-Content -Path $logFile
    }
    if (-not $warnOnly) { exit 1 }
}

function Write-Warn([string]$Message) {
    Write-Host "guard-git [OSTRZEŻENIE]: $Message" -ForegroundColor Yellow
    if ($logBlocked) {
        $logFile = Join-Path $repoRoot ".git" "guard-git.log"
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] WARN ($HookType): $Message" |
            Add-Content -Path $logFile
    }
}

# --- pre-commit: sprawdzenie staged plików ---
if ($HookType -eq "pre-commit") {
    $stagedFiles = git diff --cached --name-only 2>$null
    foreach ($file in $stagedFiles) {
        foreach ($pattern in $config.blocked_file_patterns) {
            if ($file -like $pattern) {
                Write-Blocked "próba dodania wrażliwego pliku: $file (wzorzec: $pattern)"
                Write-Host "   Usuń plik z indeksu: git reset HEAD $file" -ForegroundColor Cyan
            }
        }
    }

    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($currentBranch -in $config.protected_branches) {
        Write-Warn "commit bezpośrednio do chronionej gałęzi '$currentBranch'"
    }
}

# --- pre-push: blokada force-push do chronionych gałęzi ---
if ($HookType -eq "pre-push" -and $config.block_force_push) {
    $pushArgs = $env:GIT_PUSH_OPTION_COUNT
    $remoteName = $args[0]
    $remoteUrl  = $args[1]

    # Odczytaj stdin (format: <local_ref> <local_sha> <remote_ref> <remote_sha>)
    $pushData = $input | Select-Object -First 10
    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null

    if ($currentBranch -in $config.protected_branches) {
        # Sprawdź flagi force w zmiennych środowiskowych Git
        $gitArgs = [System.Environment]::GetCommandLineArgs() -join " "
        if ($gitArgs -match '--force|-f') {
            Write-Blocked "force-push do chronionej gałęzi '$currentBranch' jest zablokowany"
            Write-Host "   Użyj pull request zamiast force-push." -ForegroundColor Cyan
        }
    }
}

exit 0

