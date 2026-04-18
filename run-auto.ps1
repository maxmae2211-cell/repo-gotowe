param(
    [switch]$UseWslBootstrap,
    [switch]$SkipTests,
    [switch]$SkipReports,
    [int]$Timeout = 120
)

$ScriptPath = Join-Path $PSScriptRoot "scripts/full-automation.ps1"

& $ScriptPath `
    -UseWslBootstrap:$UseWslBootstrap `
    -SkipTests:$SkipTests `
    -SkipReports:$SkipReports `
    -ContinueOnReportError:$true `
    -Timeout $Timeout

exit $LASTEXITCODE
