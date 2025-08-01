@echo off
REM Development Automation Suite Launcher for Windows
REM This script helps launch the application with proper error handling

echo.
echo ============================================================
echo      Development Automation Suite - Windows Launcher
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if we're in a virtual environment
if defined VIRTUAL_ENV (
    echo 🐍 Virtual environment active: %VIRTUAL_ENV%
) else (
    echo 💡 Consider using a virtual environment:
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
)
echo.

REM Check if requirements.txt exists
if exist requirements.txt (
    echo 📦 Installing/updating dependencies...
    pip install -r requirements.txt
    echo.
) else (
    echo ⚠️  No requirements.txt found, proceeding anyway...
    echo.
)

REM Launch the application
echo 🚀 Starting Development Automation Suite...
python run.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Application failed to start
    echo Check the error messages above for details
    echo.
    pause
    exit /b 1
)

echo.
echo 👋 Application closed successfully
pause 