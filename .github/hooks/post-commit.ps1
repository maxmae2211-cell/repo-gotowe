#!/usr/bin/env pwsh
# post-commit.ps1 — Windows post-commit hook summary
# Zainstaluj przez: .github/hooks/install-hooks.ps1
# Lub ręcznie: copy .github\hooks\post-commit.ps1 .git\hooks\post-commit.ps1

$ErrorActionPreference = "SilentlyContinue"

$branch  = git rev-parse --abbrev-ref HEAD
$commit  = git rev-parse --short HEAD
$msg     = git log -1 --pretty="%s"
$files   = (git diff-tree --no-commit-id -r --name-only HEAD | Measure-Object).Count

Write-Host ""
Write-Host "✅ Commit zapisany: [$branch] $commit" -ForegroundColor Green
Write-Host "   Wiadomość : $msg"
Write-Host "   Pliki     : $files"
Write-Host ""

# Sprawdzenie wrażliwych plików
$sensitivePatterns = @("*.env", "*.pem", "*.key", ".bzt-rc", "credentials.json", "secrets.*")
$changedFiles = git diff-tree --no-commit-id -r --name-only HEAD
foreach ($file in $changedFiles) {
    foreach ($pat in $sensitivePatterns) {
        if ($file -like $pat) {
            Write-Host "⚠️  OSTRZEŻENIE: wrażliwy plik w commicie: $file" -ForegroundColor Yellow
            Write-Host "   Jeśli to pomyłka: git reset HEAD~1" -ForegroundColor Cyan
        }
    }
}
