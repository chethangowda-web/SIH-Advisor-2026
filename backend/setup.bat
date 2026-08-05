@echo off
title SIH AI Advisor - Setup
color 0B

echo.
echo  ========================================================
echo   SIH Aurora - Automated Backend Setup (Windows)
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
    echo [1/3] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created!
) else (
    echo [OK] Virtual environment already exists
)

:: Activate and install (fast set - no heavy PyTorch/ChromaDB needed)
echo.
echo [2/3] Installing packages (takes 1-2 minutes)...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Package installation failed!
    pause
    exit /b 1
)
echo [OK] Packages installed!

:: Ensure .env exists with a real GROQ_API_KEY
echo.
if not exist ".env" (
    echo [WARN] No .env found. Copying from .env.example...
    copy ".env.example" ".env" >nul
)

echo [3/3] Checking configuration...
set "HAS_KEY="
for /f "tokens=*" %%L in ('findstr /i "GROQ_API_KEY" .env') do (
    set "LINE=%%L"
)
if defined LINE if not defined HAS_KEY (
    for /f "tokens=2 delims== " %%K in ('findstr /i "GROQ_API_KEY" .env') do set "V=%%K"
)
if defined V (
    if not "%V%"=="your_groq_api_key_here" (
        echo [OK] GROQ_API_KEY is configured.
        goto :server
    )
)

echo.
echo  ========================================================
echo  GROQ_API_KEY is not set.
echo  Get a free key at:  https://console.groq.com/keys
echo  Then edit backend\.env  and set:
echo      GROQ_API_KEY=your_key_here
echo  ========================================================
echo [NOTE] The server will still start, but AI features will
echo        show a clear message until the key is added.
echo.

:server
echo.
echo  ========================================================
echo   Server running at: http://localhost:8000
echo   API docs at:       http://localhost:8000/docs
echo   Press Ctrl+C to stop
echo  ========================================================
echo.
python main.py