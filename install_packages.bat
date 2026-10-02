@echo off
cd /d c:\Users\maxma\Desktop\1.worktrees\copilot-auto-task-execution-continuous
call .venv\Scripts\python.exe -m pip install fastapi uvicorn
echo Installation complete with exit code: %ERRORLEVEL%
