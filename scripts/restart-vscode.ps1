# restart-vscode.ps1
# Restartuje VS Code i otwiera projekt repo-gotowe

param(
    [string]$ProjectPath = "C:\Users\maxma\Documents\GitHub\repo-gotowe",
    [int]$WaitSeconds = 3
)

Write-Host "Zamykam VS Code..." -ForegroundColor Yellow

# Zamknij wszystkie procesy Code.exe
Get-Process -Name "Code" -ErrorAction SilentlyContinue | Stop-Process -Force

Start-Sleep -Seconds $WaitSeconds

Write-Host "Otwieram VS Code z projektem: $ProjectPath" -ForegroundColor Green

# Otwórz VS Code z projektem
Start-Process "code" -ArgumentList $ProjectPath

Write-Host "VS Code zrestartowany." -ForegroundColor Green
