#!/usr/bin/env pwsh
# install-hooks.ps1 — instaluje Git hooks z .github/hooks/ do .git/hooks/
# Działa na wszystkich platformach (Windows, Linux, macOS) przez PowerShell Core (pwsh).
#
# Użycie (wszystkie platformy):
#   pwsh -File .github/hooks/install-hooks.ps1
#
# Windows (Windows PowerShell):
#   powershell -ExecutionPolicy Bypass -File .github\hooks\install-hooks.ps1
#
# Linux / macOS (wymaga zainstalowanego pwsh / PowerShell Core):
#   pwsh .github/hooks/install-hooks.ps1
#
# Ten plik zastępuje install-hooks.sh — nie potrzebujesz już osobnego skryptu bash.

$ErrorActionPreference = "Stop"

$repoRoot  = git rev-parse --show-toplevel
$hooksDir  = Join-Path $repoRoot ".git" "hooks"
$sourceDir = Join-Path $repoRoot ".github" "hooks"

Write-Host "Instalowanie Git hooks..." -ForegroundColor Cyan
Write-Host "  Źródło  : $sourceDir" -ForegroundColor Gray
Write-Host "  Cel     : $hooksDir" -ForegroundColor Gray
Write-Host ""

# post-commit wrapper
$postCommitWrapper = @'
#!/bin/sh
# auto-generated post-commit hook
exec "$(git rev-parse --show-toplevel)/.github/hooks/post-commit"
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

# pre-receive wrapper (server-side, do ręcznego skopiowania na serwer)
$preReceiveWrapper = @'
#!/bin/sh
# auto-generated pre-receive hook (guard-git, server-side)
if command -v pwsh >/dev/null 2>&1; then
    pwsh -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-receive
elif command -v powershell >/dev/null 2>&1; then
    powershell -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-receive
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

# pre-receive jest hookiem server-side — zapisz do katalogu hooks jako plik informacyjny
# (nie instalujemy go automatycznie do .git/hooks, bo działa tylko na serwerze)
$preReceiveDest = Join-Path $hooksDir "pre-receive.server-sample"
Set-Content -Path $preReceiveDest -Value $preReceiveWrapper -Encoding utf8 -NoNewline
Write-Host "  ℹ️  pre-receive.server-sample (wzorzec dla serwera — skopiuj ręcznie do hooks/ na serwerze)" -ForegroundColor DarkYellow

Write-Host ""
Write-Host "Gotowe! Hooks zainstalowane w: $hooksDir" -ForegroundColor Green
