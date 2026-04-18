param(
    [string]$Config = "tests\api\test-api-jmeter.yml"
)

Set-Location "C:\Users\maxma\Desktop\1"

.\.venv-taurus\Scripts\Activate.ps1

bzt $Config