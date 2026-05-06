@echo off
REM Aktywuj środowisko i uruchom automatyczny pipeline Taurus
cd /d %~dp0
call .venv\Scripts\activate
python run_and_archive.py
