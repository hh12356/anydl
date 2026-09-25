@echo off
setlocal enabledelayedexpansion
title Any Downloader Tool Setup

echo ==============================================
echo       Starting Any Downloader Tool...
echo ==============================================
echo.

cd /d "%~dp0"
set "BIN_DIR=%cd%\bin"
set "PYTHON_DIR=%BIN_DIR%\python"
set "FFMPEG_DIR=%BIN_DIR%\ffmpeg"
set PATH=%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%FFMPEG_DIR%\bin;%PATH%

if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

REM Check for FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "%FFMPEG_DIR%\bin\ffmpeg.exe" (
        echo [INFO] FFmpeg not found on system.
        echo [INFO] Downloading Portable FFmpeg ^(this only happens once^)...
        curl -L -o "%BIN_DIR%\ffmpeg.zip" "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        echo [INFO] Extracting FFmpeg...
        REM 必须用 System32 的 bsdtar（能解 zip）；直接写 tar 会命中 Git 自带的 GNU tar，它解不了 zip
        "%SystemRoot%\System32\tar.exe" -xf "%BIN_DIR%\ffmpeg.zip" -C "%BIN_DIR%"
        if exist "%FFMPEG_DIR%" rmdir /s /q "%FFMPEG_DIR%"
        ren "%BIN_DIR%\ffmpeg-master-latest-win64-gpl" "ffmpeg"
        del "%BIN_DIR%\ffmpeg.zip"
        if not exist "%FFMPEG_DIR%\bin\ffmpeg.exe" (
            echo [ERROR] ffmpeg.exe missing - check your antivirus quarantine
        ) else (
            echo [INFO] FFmpeg successfully installed locally.
        )
        echo.
    )
) else (
    echo [INFO] FFmpeg found.
)

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "%PYTHON_DIR%\python.exe" (
        echo [INFO] Python not found on system.
        echo [INFO] Downloading Portable Python 3.11 ^(this only happens once^)...
        curl -L -o "%BIN_DIR%\python.zip" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
        if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
        echo [INFO] Extracting Python...
        tar -xf "%BIN_DIR%\python.zip" -C "%PYTHON_DIR%"
        del "%BIN_DIR%\python.zip"
        
        echo [INFO] Setting up pip ^(Python Package Manager^)...
        REM Enable 'import site' so pip works in the embeddable Python
        powershell -Command "(Get-Content '%PYTHON_DIR%\python311._pth') -replace '#import site', 'import site' | Set-Content '%PYTHON_DIR%\python311._pth'"
        echo ..\..>> "%PYTHON_DIR%\python311._pth"
        
        curl -L -o "%PYTHON_DIR%\get-pip.py" "https://bootstrap.pypa.io/get-pip.py"
        "%PYTHON_DIR%\python.exe" "%PYTHON_DIR%\get-pip.py" --no-warn-script-location
        echo [INFO] Portable Python setup complete.
        echo.
    )
    set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
) else (
    echo [INFO] Python found.
    set "PYTHON_EXE=python"
)

REM Set up dependencies
if "%PYTHON_EXE%"=="python" (
    REM If using system python, we use a virtual environment to avoid polluting their system
    if not exist ".venv" (
        echo [INFO] Creating virtual environment...
        python -m venv .venv
    )
    call .venv\Scripts\activate.bat
    set "ACTUAL_PYTHON=python"
) else (
    REM If using portable python, it's already isolated, no venv needed
    set "ACTUAL_PYTHON=%PYTHON_EXE%"
)

echo [INFO] Checking dependencies...
%ACTUAL_PYTHON% -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo.
echo ==============================================
echo       Launching Application in Browser!
echo ==============================================
%ACTUAL_PYTHON% main.py

pause
