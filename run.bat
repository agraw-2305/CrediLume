@echo off
setlocal
cd /d "%~dp0"

set "PORT=5000"

REM Kill any process already using the port (prevents stuck/duplicate servers)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr LISTENING') do (
  echo Stopping process on port %PORT% (PID %%a)...
  taskkill /PID %%a /F >nul 2>&1
)

echo Starting CrediLume Flask server on http://127.0.0.1:%PORT%
echo.

if exist ".venv\Scripts\python.exe" (
  set "FLASK_DEBUG=1"
  set "FLASK_RELOADER=1"
  ".venv\Scripts\python.exe" app.py
) else (
  echo WARNING: .venv not found. Falling back to system Python.
  set "FLASK_DEBUG=1"
  set "FLASK_RELOADER=1"
  python app.py
)
