param(
    [switch]$PurgeRunmeJdkCache = $true
)

$ErrorActionPreference = 'Stop'

$runmeBase = Join-Path $env:APPDATA 'Code/User/globalStorage/stateful.runme'
$jdkPath = 'C:/Program Files/Eclipse Adoptium/jdk-21.0.2.13-hotspot'

Write-Host '[1/4] Stopping stale Java processes...'
Get-Process java, javaw, jshell -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host '[2/4] Checking system JDK 21...'
if (-not (Test-Path (Join-Path $jdkPath 'bin/java.exe'))) {
    throw "System JDK not found at: $jdkPath"
}

Write-Host '[3/4] Verifying Java/JShell from JDK 21...'
& (Join-Path $jdkPath 'bin/java.exe') -version
& (Join-Path $jdkPath 'bin/jshell.exe') --version

if ($PurgeRunmeJdkCache -and (Test-Path $runmeBase)) {
    Write-Host '[4/4] Purging Runme bundled openJDK cache...'
    Get-ChildItem $runmeBase -Directory -ErrorAction SilentlyContinue |
        ForEach-Object {
            $openJdkDir = Join-Path $_.FullName 'openJdk-25'
            if (Test-Path $openJdkDir) {
                Remove-Item $openJdkDir -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "Removed: $openJdkDir"
            }
        }
} else {
    Write-Host '[4/4] Skipping Runme openJDK cache purge.'
}

Write-Host ''
Write-Host 'Done. Next in VS Code:'
Write-Host '1) Developer: Reload Window'
Write-Host '2) Re-open the notebook'
Write-Host '3) Select Java kernel again'
