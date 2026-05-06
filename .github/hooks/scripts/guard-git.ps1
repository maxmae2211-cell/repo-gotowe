# guard-git.ps1 — Blokuje niebezpieczne komendy git
# Użycie: . .github/hooks/scripts/guard-git.ps1
# Następnie wywołaj: Invoke-GuardGit "git push --force"

param(
    [string]$Command = ""
)

$configPath = Join-Path $PSScriptRoot ".." "guard-git.json"
if (-not (Test-Path $configPath)) {
    Write-Warning "guard-git.json nie znaleziony: $configPath"
    exit 0
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json

function Invoke-GuardGit {
    param([string]$Cmd)

    foreach ($pattern in $config.blocked_patterns) {
        if ($Cmd -like "*$pattern*") {
            Write-Error "❌ ZABLOKOWANO: '$Cmd' pasuje do wzorca '$pattern'"
            Write-Error "Ta komenda jest oznaczona jako niebezpieczna w guard-git.json"
            exit 1
        }
    }

    foreach ($pattern in $config.warning_patterns) {
        if ($Cmd -like "*$pattern*") {
            Write-Warning "⚠️  OSTRZEŻENIE: '$Cmd' pasuje do wzorca '$pattern'"
            Write-Warning "Upewnij się, że wiesz co robisz."
        }
    }

    Write-Host "✅ Komenda dozwolona: $Cmd"
}

if ($Command) {
    Invoke-GuardGit $Command
}
