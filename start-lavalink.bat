@echo off
title Void Vibe - Lavalink Audio Server
cd /d "%~dp0"

echo =======================================================
echo          Void Vibe - Lavalink Audio Server
echo        Tagline: [Your soundtrack, your server.]
echo =======================================================
echo.

:: 1. Verify Java Installation
where java >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Java is not installed or not found on PATH.
    echo Please install Java 17+ or 21 LTS from https://adoptium.net/
    echo and ensure "Add to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Verify Lavalink.jar
if not exist "Lavalink.jar" (
    echo [ERROR] Lavalink.jar not found in: %cd%
    echo Please ensure Lavalink.jar is placed in this directory.
    echo.
    pause
    exit /b 1
)

:: 3. Verify application.yml
if not exist "application.yml" (
    echo [ERROR] application.yml not found in: %cd%
    echo.
    pause
    exit /b 1
)

:: 4. Load environment variables from .env if present
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
)

echo Starting Lavalink Server...
echo.
java -jar .\Lavalink.jar

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Lavalink exited with code %ERRORLEVEL%.
    pause
)
