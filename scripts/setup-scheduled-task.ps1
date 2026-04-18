# Create Windows Scheduled Task for automatic test execution
# Run as Administrator

param(
    [string]$ProjectRoot = "C:\Users\maxma\Desktop\1",
    [string]$TaskName = "Taurus-Auto-Tests",
    [string]$Schedule = "DAILY",
    [string]$Time = "02:00:00"
)

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must run as Administrator" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Creating Scheduled Task: $TaskName" -ForegroundColor Cyan

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Start-Sleep -Seconds 2
}

# Create task trigger
$trigger = New-ScheduledTaskTrigger -Daily -At $Time

# Create task action
$scriptPath = Join-Path $ProjectRoot "scripts\auto-execute.ps1"
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Silent"

# Create task principal
$principal = New-ScheduledTaskPrincipal `
    -UserID "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Create task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Register task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $trigger `
        -Action $action `
        -Principal $principal `
        -Settings $settings `
        -Description "Automatic Taurus Performance Test Execution" `
        -Force | Out-Null
    
    Write-Host "✓ Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Schedule: $Schedule at $Time"
    Write-Host "  Script: $scriptPath"
    Write-Host "  Status: ACTIVE"
    Write-Host ""
    Write-Host "View task: Open Task Scheduler and search for '$TaskName'" -ForegroundColor Yellow
}
catch {
    Write-Host "ERROR: Failed to create task" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""
Write-Host "Setup complete! Tests will run automatically." -ForegroundColor Green
