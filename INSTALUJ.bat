@echo off
title Instalator Crypto Auto Trader
echo.
echo ====================================================
echo   Crypto Auto Trader - Instalator Windows
echo ====================================================
echo.

:: Pobierz i uruchom skrypt PowerShell z GitHub
set "RAW_URL=https://raw.githubusercontent.com/maxmae2211-cell/repo-gotowe/main/install_windows.ps1"
set "TARGET_PS1=%TEMP%\install_trader_latest.ps1"
if exist "%TARGET_PS1%" del /f /q "%TARGET_PS1%"
powershell -ExecutionPolicy Bypass -Command "& { $url = '%RAW_URL%?ts=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile '%TARGET_PS1%'; & '%TARGET_PS1%' }"

pause
