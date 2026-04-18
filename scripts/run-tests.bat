@echo off
REM Test Runner Script - Batch version

echo.
echo ==========================================
echo Taurus Load Testing Suite
echo ==========================================
echo Project: %CD%
echo.

REM Start mock API server
echo Starting mock API server...
start /B python scripts\mock-api-server.py
timeout /t 2 /nobreak

REM Run tests
echo Found 7 API tests
echo.

setlocal enabledelayedexpansion
set passed=0
set failed=0

for %%f in (tests\api\test-api-*.yml) do (
    echo ----------------------------------------
    echo Running: %%~nf
    echo ----------------------------------------
    
    bzt %%f
    if !errorlevel! equ 0 (
        echo [OK] PASSED: %%~nf
        set /a passed=!passed!+1
    ) else (
        echo [ERROR] FAILED: %%~nf
        set /a failed=!failed!+1
    )
    echo.
)

REM Stop server
echo Stopping mock API server...
taskkill /FI "WINDOWTITLE eq Python*" /T /F 2>nul

echo.
echo ==========================================
echo Test Summary
echo ==========================================
echo Total Tests: 7
echo Passed: !passed!
echo Failed: !failed!
echo ==========================================

endlocal
