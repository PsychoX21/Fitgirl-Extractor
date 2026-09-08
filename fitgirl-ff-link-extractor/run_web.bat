@echo off
setlocal enabledelayedexpansion
title FitGirl Direct Link Extractor - Web Server

echo =======================================================
echo   FitGirl Direct Link Extractor Web Server
echo =======================================================
echo.

set "PYTHON_CMD="

if exist "%USERPROFILE%\anaconda3\python.exe" (
    set "PYTHON_CMD=%USERPROFILE%\anaconda3\python.exe"
    goto :check_deps
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :check_deps
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :check_deps
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :check_deps
)

echo [ERROR] Python was not found on your system!
echo Please make sure Python 3.10+ or Anaconda is installed.
pause
exit /b 1

:check_deps
echo [1/3] Using Python: !PYTHON_CMD!

!PYTHON_CMD! -c "import fastapi, uvicorn, bs4, requests, selenium, undetected_chromedriver" >nul 2>&1
if %errorlevel% neq 0 (
    echo [2/3] Installing missing packages...
    !PYTHON_CMD! -m pip install -r requirements.txt
) else (
    echo [2/3] All dependencies are ready.
)

echo [3/3] Starting web server on http://127.0.0.1:8000 ...
echo.
echo Opening browser...
start http://127.0.0.1:8000

!PYTHON_CMD! app.py

pause
