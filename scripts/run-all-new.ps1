Write-Host "=== RUN ALL TESTS ==="

$tests = Get-ChildItem "C:\Users\maxma\Desktop\1\tests" -Filter *.yaml

& "C:\Users\maxma\Desktop\1\.venv\Scripts\Activate.ps1"

foreach ($t in $tests) {
    Write-Host "Running: $($t.Name)"
    bzt $t.FullName
}