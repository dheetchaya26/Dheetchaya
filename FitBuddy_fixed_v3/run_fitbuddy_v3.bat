@echo off
setlocal EnableExtensions EnableDelayedExpansion
title FitBuddy - Fixed V3

echo ============================================================
echo        FitBuddy - Fixed V3 Setup and Run
echo ============================================================
echo.

for %%I in ("%~dp0.") do set "SCRIPT_DIR=%%~fI"
set "PROJECT_DIR="

if exist "%SCRIPT_DIR%\fitbuddy\requirements.txt" if exist "%SCRIPT_DIR%\fitbuddy\app\main.py" set "PROJECT_DIR=%SCRIPT_DIR%\fitbuddy"
if not defined PROJECT_DIR if exist "%SCRIPT_DIR%\requirements.txt" if exist "%SCRIPT_DIR%\app\main.py" set "PROJECT_DIR=%SCRIPT_DIR%"

if not defined PROJECT_DIR (
  echo [ERROR] fitbuddy project folder not found.
  pause
  exit /b 1
)

cd /d "%PROJECT_DIR%"
echo [OK] Project folder: %CD%
echo.

set "PY_EXE="
for /f "usebackq delims=" %%P in (`py -3.12 -c "import sys; print(sys.executable)" 2^>nul`) do if not defined PY_EXE set "PY_EXE=%%P"
for /f "usebackq delims=" %%P in (`py -3 -c "import sys; print(sys.executable)" 2^>nul`) do if not defined PY_EXE set "PY_EXE=%%P"
for /f "usebackq delims=" %%P in (`python -c "import sys; print(sys.executable)" 2^>nul`) do if not defined PY_EXE set "PY_EXE=%%P"

if not defined PY_EXE (
  echo [ERROR] Python 3 was not found.
  echo Install Python 3.12 and run this file again.
  pause
  exit /b 1
)

echo [OK] Python:
"%PY_EXE%" --version
echo.

if not exist "venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment...
  "%PY_EXE%" -m venv venv
  if errorlevel 1 (
    echo [ERROR] Could not create virtual environment.
    pause
    exit /b 1
  )
)

set "VENV_PY=%CD%\venv\Scripts\python.exe"

echo [INFO] Installing/updating required packages...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Package installation failed.
  pause
  exit /b 1
)

if not exist ".env" (
  echo.
  echo A Gemini API key is needed for real AI generation.
  echo Press ENTER to use fallback/demo mode.
  set /p "GEMINI_KEY=Paste Gemini API key: "
  if defined GEMINI_KEY (
    >".env" echo GOOGLE_API_KEY=!GEMINI_KEY!
    echo [OK] API key saved in .env
  )
)

if not exist "static\images" mkdir "static\images"

echo.
echo [INFO] Checking the application...
"%VENV_PY%" -m compileall -q app
if errorlevel 1 (
  echo [ERROR] Python syntax check failed.
  pause
  exit /b 1
)

"%VENV_PY%" -c "import app.main; print('[OK] FitBuddy imported successfully.')"
if errorlevel 1 (
  echo [ERROR] FitBuddy import failed. Copy the error above.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo FitBuddy is starting.
echo Home   : http://127.0.0.1:8000
echo Health : http://127.0.0.1:8000/health
echo Docs   : http://127.0.0.1:8000/docs
echo Admin  : http://127.0.0.1:8000/view-all-users
echo.
echo When Generate Plan is clicked, the button will show
echo "Generating plan...". AI calls have a timeout so the page
echo will no longer wait forever.
echo ============================================================
echo.

start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000"
"%VENV_PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
