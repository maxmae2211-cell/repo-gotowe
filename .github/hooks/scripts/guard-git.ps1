#!/usr/bin/env pwsh
# guard-git.ps1 - checks staged files and protected branch push rules

param(
    [ValidateSet("pre-commit", "pre-push", "pre-receive")]
    [string]$HookType = "pre-commit"
)

$ErrorActionPreference = "Stop"
$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { $repoRoot = (Get-Location).Path }

$configPath = Join-Path (Join-Path $PSScriptRoot "..") "guard-git.json"
if (-not (Test-Path $configPath)) {
    $configPath = Join-Path (Join-Path (Join-Path $repoRoot ".github") "hooks") "guard-git.json"
}

if (-not (Test-Path $configPath)) {
    Write-Warning "guard-git: missing config file $configPath - hook skipped."
    exit 0
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$warnOnly = [bool]$config.warn_only
$logBlocked = [bool]$config.log_blocked
$maxFileSizeKb = if ($null -ne $config.max_file_size_kb) { [int]$config.max_file_size_kb } else { 0 }
$requireConventional = if ($null -ne $config.require_conventional_commits) { [bool]$config.require_conventional_commits } else { $false }
$blockedMsgPatterns = if ($config.blocked_commit_message_patterns) { $config.blocked_commit_message_patterns } else { @() }

function Write-Blocked([string]$Message) {
    Write-Host "guard-git [BLOCKED]: $Message" -ForegroundColor Red
    if ($logBlocked) {
        $logFile = Join-Path (Join-Path $repoRoot ".git") "guard-git.log"
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] BLOCKED ($HookType): $Message" | Add-Content -Path $logFile
    }
    if (-not $warnOnly) { exit 1 }
}

function Write-Warn([string]$Message) {
    Write-Host "guard-git [WARN]: $Message" -ForegroundColor Yellow
    if ($logBlocked) {
        $logFile = Join-Path (Join-Path $repoRoot ".git") "guard-git.log"
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] WARN ($HookType): $Message" | Add-Content -Path $logFile
    }
}

if ($HookType -eq "pre-commit") {
    $stagedFiles = git diff --cached --name-only 2>$null
    foreach ($file in $stagedFiles) {
        foreach ($pattern in $config.blocked_file_patterns) {
            if ($file -like $pattern) {
                Write-Blocked "attempt to add sensitive file: $file (pattern: $pattern)"
                Write-Host "   Remove from index: git reset HEAD $file" -ForegroundColor Cyan
            }
        }

        if ($maxFileSizeKb -gt 0) {
            $fullPath = Join-Path $repoRoot $file
            if (Test-Path $fullPath) {
                $sizeKb = [math]::Round((Get-Item $fullPath).Length / 1KB, 1)
                if ($sizeKb -gt $maxFileSizeKb) {
                    Write-Blocked "file '$file' is too large: ${sizeKb} KB (limit: ${maxFileSizeKb} KB)"
                    Write-Host "   Consider Git LFS for large binary files." -ForegroundColor Cyan
                }
            }
        }
    }

    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($currentBranch -in $config.protected_branches) {
        Write-Warn "commit directly on protected branch '$currentBranch'"
    }

    $commitMsgFile = Join-Path (Join-Path $repoRoot ".git") "COMMIT_EDITMSG"
    if (Test-Path $commitMsgFile) {
        $commitMsg = (Get-Content $commitMsgFile -Raw).Trim()

        foreach ($pattern in $blockedMsgPatterns) {
            if ($commitMsg -match $pattern) {
                Write-Blocked "commit message matches blocked pattern '$pattern': $commitMsg"
                Write-Host "   Change the commit message before pushing." -ForegroundColor Cyan
            }
        }

        if ($requireConventional) {
            $conventionalPattern = '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?: .+'
            if ($commitMsg -notmatch $conventionalPattern) {
                Write-Blocked "commit message is not Conventional Commits compliant: '$commitMsg'"
                Write-Host "   Required format: type(scope): description (e.g. feat: add new feature)" -ForegroundColor Cyan
            }
        }
    }
}

if ($HookType -eq "pre-receive") {
    $refLines = @($input)
    foreach ($line in $refLines) {
        $parts = $line -split '\s+'
        if ($parts.Count -lt 3) { continue }

        $oldSha = $parts[0]
        $newSha = $parts[1]
        $ref = $parts[2]
        $branchName = $ref -replace '^refs/heads/', ''

        $zeroSha = "0000000000000000000000000000000000000000"
        if ($config.block_force_push -and $oldSha -ne $zeroSha -and $newSha -ne $zeroSha) {
            if ($branchName -in $config.protected_branches) {
                $mergeBase = git merge-base $oldSha $newSha 2>$null
                if ($mergeBase -ne $oldSha) {
                    Write-Blocked "server: force-push to protected branch '$branchName' is blocked ($oldSha -> $newSha)"
                    Write-Host "   Use a pull request instead of force-push." -ForegroundColor Cyan
                }
            }
        }

        if ($oldSha -eq $zeroSha) {
            $newCommits = git log --format="%H %s" $newSha 2>$null | Select-Object -First 50
        }
        else {
            $newCommits = git log --format="%H %s" "${oldSha}..${newSha}" 2>$null
        }

        foreach ($commitLine in $newCommits) {
            $sha = ($commitLine -split ' ')[0]
            $msg = $commitLine.Substring([Math]::Min($sha.Length + 1, $commitLine.Length))

            foreach ($pattern in $blockedMsgPatterns) {
                if ($msg -match $pattern) {
                    Write-Blocked "server: commit $($sha.Substring(0,8)) message blocked by '$pattern': $msg"
                }
            }

            if ($requireConventional) {
                $ccPattern = '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?: .+'
                if ($msg -notmatch $ccPattern) {
                    Write-Blocked "server: commit $($sha.Substring(0,8)) not Conventional Commits compliant: '$msg'"
                    Write-Host "   Required format: type(scope): description" -ForegroundColor Cyan
                }
            }
        }
    }
}

if ($HookType -eq "pre-push" -and $config.block_force_push) {
    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($currentBranch -in $config.protected_branches) {
        $gitArgs = [System.Environment]::GetCommandLineArgs() -join " "
        if ($gitArgs -match '--force|-f') {
            Write-Blocked "force-push to protected branch '$currentBranch' is blocked"
            Write-Host "   Use a pull request instead of force-push." -ForegroundColor Cyan
        }
    }
}

exit 0
