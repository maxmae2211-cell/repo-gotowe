@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m pip install fastapi uvicorn requests bzt selenium locust
) else if exist ".venv-taurus\Scripts\python.exe" (
    .venv-taurus\Scripts\python.exe -m pip install fastapi uvicorn requests bzt selenium locust
) else (
    python -m pip install fastapi uvicorn requests bzt selenium locust
)
echo Installation complete with exit code: %ERRORLEVEL%
