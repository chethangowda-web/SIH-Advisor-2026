@echo off
title SIH AI Advisor - Setup
color 0B

echo.
echo  ========================================================
echo   SIH AI Advisor - Automated Backend Setup (Windows)
echo  ========================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install from python.org
    pause
    exit /b 1
)
echo [OK] Python found!

:: Create venv if not exists
if not exist "venv" (
    echo.
    echo [1/4] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created!
) else (
    echo [OK] Virtual environment already exists
)

:: Activate and install
echo.
echo [2/4] Installing Python packages (this takes 3-5 minutes)...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Package installation failed!
    pause
    exit /b 1
)
echo [OK] All packages installed!

:: Run data pipeline
echo.
echo [3/4] Building AI vector database (first time only)...
python data_pipeline.py
if %errorlevel% neq 0 (
    echo [ERROR] Data pipeline failed!
    pause
    exit /b 1
)
echo [OK] Vector database ready!

:: Start server
echo.
echo [4/4] Starting SIH AI Advisor server...
echo.
echo  ========================================================
echo   Server running at: http://localhost:8000
echo   API docs at:       http://localhost:8000/docs
echo   Press Ctrl+C to stop
echo  ========================================================
echo.
python main.py
