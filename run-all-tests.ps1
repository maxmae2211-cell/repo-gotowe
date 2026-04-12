$tests = @(
    "test-smoke.yaml",
    "test-basic.yaml",
    "test-api-load.yaml",
    "test-ramp.yaml",
    "test-multi-endpoints.yaml",
    "test-local-api.yaml",
    "test-heavy.yaml",
    "test-with-report.yaml"
)

foreach ($test in $tests) {
    Write-Host "========================================="
    Write-Host "Running test: $test"
    Write-Host "========================================="

    docker-compose run --rm taurus "/bzt-configs/$test"

    Write-Host "Finished: $test"
    Write-Host ""
}