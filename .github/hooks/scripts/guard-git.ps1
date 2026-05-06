#!/usr/bin/env pwsh
# guard-git.ps1 — blokuje wrażliwe pliki w staged (pre-commit)
#                 oraz blokuje force-push do chronionych gałęzi (pre-push)
# Zainstaluj przez: .github/hooks/install-hooks.ps1

param(
    [ValidateSet("pre-commit", "pre-push", "pre-receive")]
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
$maxFileSizeKb = if ($null -ne $config.max_file_size_kb) { [int]$config.max_file_size_kb } else { 0 }
$requireConventional = if ($null -ne $config.require_conventional_commits) { [bool]$config.require_conventional_commits } else { $false }
$blockedMsgPatterns  = if ($config.blocked_commit_message_patterns) { $config.blocked_commit_message_patterns } else { @() }

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
        # Sprawdź wzorce wrażliwych plików
        foreach ($pattern in $config.blocked_file_patterns) {
            if ($file -like $pattern) {
                Write-Blocked "próba dodania wrażliwego pliku: $file (wzorzec: $pattern)"
                Write-Host "   Usuń plik z indeksu: git reset HEAD $file" -ForegroundColor Cyan
            }
        }

        # Sprawdź rozmiar pliku
        if ($maxFileSizeKb -gt 0) {
            $fullPath = Join-Path $repoRoot $file
            if (Test-Path $fullPath) {
                $sizeKb = [math]::Round((Get-Item $fullPath).Length / 1KB, 1)
                if ($sizeKb -gt $maxFileSizeKb) {
                    Write-Blocked "plik '$file' jest za duży: ${sizeKb} KB (limit: ${maxFileSizeKb} KB)"
                    Write-Host "   Rozważ użycie Git LFS dla dużych plików binarnych." -ForegroundColor Cyan
                }
            }
        }
    }

    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($currentBranch -in $config.protected_branches) {
        Write-Warn "commit bezpośrednio do chronionej gałęzi '$currentBranch'"
    }

    # Sprawdź treść wiadomości commitu
    $commitMsgFile = Join-Path $repoRoot ".git" "COMMIT_EDITMSG"
    if (Test-Path $commitMsgFile) {
        $commitMsg = (Get-Content $commitMsgFile -Raw).Trim()

        # Zablokowane wzorce wiadomości
        foreach ($pattern in $blockedMsgPatterns) {
            if ($commitMsg -match $pattern) {
                Write-Blocked "wiadomość commitu pasuje do zablokowanego wzorca '$pattern': $commitMsg"
                Write-Host "   Zmień wiadomość commitu przed wypchnięciem." -ForegroundColor Cyan
            }
        }

        # Wymagany format Conventional Commits
        if ($requireConventional) {
            $conventionalPattern = '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?: .+'
            if ($commitMsg -notmatch $conventionalPattern) {
                Write-Blocked "wiadomość commitu nie jest zgodna z Conventional Commits: '$commitMsg'"
                Write-Host "   Wymagany format: type(scope): opis  (np. feat: dodaj nową funkcję)" -ForegroundColor Cyan
            }
        }
    }
}

# --- pre-receive: server-side blokada force-push i wzorców commitów ---
if ($HookType -eq "pre-receive") {
    # pre-receive czyta ze stdin: <old-sha> <new-sha> <ref>
    $refLines = @($input)
    foreach ($line in $refLines) {
        $parts = $line -split '\s+'
        if ($parts.Count -lt 3) { continue }
        $oldSha = $parts[0]
        $newSha = $parts[1]
        $ref    = $parts[2]

        # Wyodrębnij nazwę gałęzi z pełnej referencji (refs/heads/main -> main)
        $branchName = $ref -replace '^refs/heads/', ''

        # Blokuj force-push (old SHA != 0000... i new SHA nie jest potomkiem old SHA)
        $zeroSha = "0000000000000000000000000000000000000000"
        if ($config.block_force_push -and $oldSha -ne $zeroSha -and $newSha -ne $zeroSha) {
            if ($branchName -in $config.protected_branches) {
                # Sprawdź czy new jest potomkiem old (force-push = new NIE jest potomkiem old)
                $mergeBase = git merge-base $oldSha $newSha 2>$null
                if ($mergeBase -eq $oldSha) {
                    # old jest przodkiem new — normalny push, OK
                } else {
                    # old NIE jest przodkiem new — force-push
                    Write-Blocked "server: force-push do chronionej gałęzi '$branchName' jest zablokowany (SHA: $oldSha -> $newSha)"
                    Write-Host "   Użyj pull request zamiast force-push." -ForegroundColor Cyan
                }
            }
        }

        # Sprawdź wiadomości commitów w nowo pushowanych commitach
        if ($oldSha -eq $zeroSha) {
            # Nowa gałąź — sprawdź ostatnie 50 commitów
            $newCommits = git log --format="%H %s" $newSha 2>$null | Select-Object -First 50
        } else {
            # Istniejąca gałąź — sprawdź tylko nowe commity
            $newCommits = git log --format="%H %s" "${oldSha}..${newSha}" 2>$null
        }

        foreach ($commitLine in $newCommits) {
            $sha = ($commitLine -split ' ')[0]
            $msg = $commitLine.Substring([Math]::Min($sha.Length + 1, $commitLine.Length))

            foreach ($pattern in $blockedMsgPatterns) {
                if ($msg -match $pattern) {
                    Write-Blocked "server: commit $($sha.Substring(0,8)) ma zablokowaną wiadomość '$pattern': $msg"
                }
            }

            if ($requireConventional) {
                $ccPattern = '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?: .+'
                if ($msg -notmatch $ccPattern) {
                    Write-Blocked "server: commit $($sha.Substring(0,8)) nie spełnia Conventional Commits: '$msg'"
                    Write-Host "   Wymagany format: type(scope): opis  (np. feat: nowa funkcja)" -ForegroundColor Cyan
                }
            }
        }
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

