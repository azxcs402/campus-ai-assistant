@echo off
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
  echo Please create the backend virtual environment first.
  exit /b 1
)
call .venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
