@echo off
cd /d "%~dp0"
python -m venv Python\.venv
if errorlevel 1 exit /b 1
Python\.venv\Scripts\python.exe -m pip install -r Python\requirements.txt
pause
