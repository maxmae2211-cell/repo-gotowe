@echo off
REM Auto-execution startup script for Taurus Test Suite
REM Runs automatically on Windows startup

setlocal enabledelayedexpansion

REM Get project root
cd /d %~dp0..
set PROJECT_ROOT=%cd%

REM Log file
set LOG_FILE=%PROJECT_ROOT%\logs\auto-exec-%date:~10,4%%date:~4,2%%date:~7,2%-%time:~0,2%%time:~3,2%%time:~6,2%.log

REM Create logs directory
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

echo [%date% %time%] Starting automatic test execution >> "%LOG_FILE%"
echo Project: %PROJECT_ROOT% >> "%LOG_FILE%"

REM Run Python tests
echo [%date% %time%] Running Python test suite >> "%LOG_FILE%"
python "%PROJECT_ROOT%\scripts\run-tests.py" >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [%date% %time%] Tests FAILED >> "%LOG_FILE%"
    exit /b 1
) else (
    echo [%date% %time%] Tests PASSED >> "%LOG_FILE%"
    exit /b 0
)
