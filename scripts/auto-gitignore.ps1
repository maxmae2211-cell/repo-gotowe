param(
    [string]$Branch = "qq",
    [string]$Message = "Update .gitignore",
    [string]$TargetFile = ".gitignore"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path $TargetFile)) {
    throw "Nie znaleziono pliku: $TargetFile"
}

git rev-parse --is-inside-work-tree 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "To nie jest repozytorium Git: $repoRoot"
}

$current = (git rev-parse --abbrev-ref HEAD).Trim()
if ($current -ne $Branch) {
    git checkout $Branch
}

git add -- $TargetFile
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m $Message
    git push origin $Branch
    Write-Host "Zrobiono commit + push na '$Branch'."
} else {
    Write-Host "Brak zmian w $TargetFile do commita."
}

git status --short