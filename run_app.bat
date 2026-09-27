@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Expense Tracker - First Time Setup
echo ============================================

if not exist ".venv\Scripts\python.exe" (
    echo Creating private Python environment...
    where py >nul 2>&1
    if %errorlevel%==0 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 (
        echo.
        echo ERROR: Python 3 could not be found.
        echo Install Python 3.10+ and run this file again.
        pause
        exit /b 1
    )
)

echo Installing/checking required packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Package installation failed.
    echo Check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo Starting Expense Tracker...
.venv\Scripts\python.exe -m streamlit run main.py
pause
