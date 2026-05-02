#!/usr/bin/env pwsh
# install-hooks.ps1 — instaluje Git hooks z .github/hooks/ do .git/hooks/
# Uruchom z katalogu głównego repozytorium:
#   powershell -ExecutionPolicy Bypass -File .github\hooks\install-hooks.ps1

$ErrorActionPreference = "Stop"

$repoRoot  = git rev-parse --show-toplevel
$hooksDir  = Join-Path $repoRoot ".git" "hooks"
$sourceDir = Join-Path $repoRoot ".github" "hooks"

Write-Host "Instalowanie Git hooks..." -ForegroundColor Cyan
Write-Host "  Źródło  : $sourceDir" -ForegroundColor Gray
Write-Host "  Cel     : $hooksDir" -ForegroundColor Gray
Write-Host ""

# post-commit (PowerShell wrapper)
$postCommitWrapper = @'
#!/bin/sh
# auto-generated post-commit hook
if command -v pwsh >/dev/null 2>&1; then
    pwsh -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/post-commit.ps1"
elif command -v powershell >/dev/null 2>&1; then
    powershell -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/post-commit.ps1"
else
    "$(git rev-parse --show-toplevel)/.github/hooks/post-commit"
fi
'@

# pre-commit (guard-git wrapper)
$preCommitWrapper = @'
#!/bin/sh
# auto-generated pre-commit hook (guard-git)
if command -v pwsh >/dev/null 2>&1; then
    pwsh -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-commit
elif command -v powershell >/dev/null 2>&1; then
    powershell -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-commit
fi
'@

# pre-push (guard-git wrapper)
$prePushWrapper = @'
#!/bin/sh
# auto-generated pre-push hook (guard-git)
if command -v pwsh >/dev/null 2>&1; then
    pwsh -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-push "$1" "$2"
elif command -v powershell >/dev/null 2>&1; then
    powershell -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-push "$1" "$2"
fi
'@

function Install-Hook {
    param([string]$Name, [string]$Content)
    $dest = Join-Path $hooksDir $Name
    Set-Content -Path $dest -Value $Content -Encoding utf8 -NoNewline
    # chmod +x na systemach Unix
    if ($IsLinux -or $IsMacOS) {
        chmod +x $dest
    }
    Write-Host "  ✅ $Name" -ForegroundColor Green
}

Install-Hook "post-commit" $postCommitWrapper
Install-Hook "pre-commit"  $preCommitWrapper
Install-Hook "pre-push"    $prePushWrapper

Write-Host ""
Write-Host "Gotowe! Hooks zainstalowane w: $hooksDir" -ForegroundColor Green
