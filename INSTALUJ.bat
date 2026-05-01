@echo off
title Instalator Crypto Auto Trader
echo.
echo ====================================================
echo   Crypto Auto Trader - Instalator Windows
echo ====================================================
echo.

:: Pobierz i uruchom skrypt PowerShell z GitHub
powershell -ExecutionPolicy Bypass -Command "& {Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/maxmae2211-cell/repo-gotowe/main/install_windows.ps1' -OutFile '%TEMP%\install_trader.ps1'; & '%TEMP%\install_trader.ps1'}"

pause
