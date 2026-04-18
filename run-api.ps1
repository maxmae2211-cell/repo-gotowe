param(
    [int]$Port = 8000
)

Set-Location "C:\Users\maxma\Desktop\1"

.\.venv-taurus\Scripts\Activate.ps1

Set-Location ".\api"

uvicorn main:app --reload --port $Port