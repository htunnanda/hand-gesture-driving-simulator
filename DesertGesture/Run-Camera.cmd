@echo off
cd /d "%~dp0"
if not exist Python\.venv\Scripts\python.exe (
  echo Run Setup-Python.cmd first using Python 3.11 or 3.12.
  pause
  exit /b 1
)
Python\.venv\Scripts\python.exe Python\bridge.py --preview
pause
