@echo off
REM Alnoor Medical Services - API Server Startup Script
REM This script starts the API server using your project's virtual environment

echo ============================================================
echo Alnoor Medical Services - API Server Startup
echo ============================================================
echo.

REM Check if we're in the alnoor-tracing directory
if not exist "src\api_server.py" (
    echo ERROR: Cannot find src\api_server.py
    echo.
    echo Please run this script from the alnoor-tracing directory
    echo or copy the entire alnoor-tracing folder to use the server.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist ".venv\Scripts\python.exe" (
    echo Using project virtual environment
    set PYTHON_CMD=.venv\Scripts\python.exe
    goto :start_server
)

REM If no venv, try to find Python and create one
echo No virtual environment found. Creating one...
echo.

REM Find Python
set PYTHON_FOUND=0
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "python"
) do (
    if exist %%~P (
        %%~P --version >nul 2>&1
        if not errorlevel 1 (
            echo Found Python: %%~P
            %%~P -m venv .venv
            if not errorlevel 1 (
                set PYTHON_CMD=.venv\Scripts\python.exe
                set PYTHON_FOUND=1
                goto :install_deps
            )
        )
    )
)

if %PYTHON_FOUND%==0 (
    echo ERROR: Could not find working Python installation
    echo.
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:install_deps
echo.
echo Installing dependencies...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install flask flask-cors sqlalchemy

:start_server
echo.
echo ============================================================
echo Starting API Server
echo ============================================================
echo.

%PYTHON_CMD% --version
echo.

echo Server will run on: http://0.0.0.0:5000
echo Other computers can connect using: http://YOUR-IP-ADDRESS:5000
echo.
echo To find your IP: ipconfig (look for IPv4 Address)
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

%PYTHON_CMD% src\api_server.py

pause
