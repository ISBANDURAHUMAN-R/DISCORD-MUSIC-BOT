@echo off
title Void Vibe - Discord Music Bot
cd /d "%~dp0"

echo =======================================================
echo            Void Vibe - Discord Music Bot
echo         Tagline: [Your soundtrack, your server.]
echo =======================================================
echo.

:: 1. Verify .env file exists
if not exist ".env" (
    echo [ERROR] Configuration file '.env' not found in: %cd%
    echo Please copy '.env.example' to '.env' and configure your DISCORD_TOKEN.
    echo.
    pause
    exit /b 1
)

:: 2. Locate Python executable (prefer virtual environment)
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo Using virtual environment Python: .venv
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python is not installed or not found on PATH.
        echo Please install Python 3.12+ from https://python.org/
        echo.
        pause
        exit /b 1
    )
    set "PYTHON_EXE=python"
    echo Using system Python.
)

:: 3. Run the Bot
echo Starting Void Vibe bot...
echo.
"%PYTHON_EXE%" bot.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Bot exited with code %ERRORLEVEL%.
    pause
)
