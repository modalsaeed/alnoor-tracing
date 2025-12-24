@echo off
REM Alnoor Medical Services - API Server Startup Script
REM This script starts the API server for multi-user database access

echo ============================================================
echo Alnoor Medical Services - API Server Startup
echo ============================================================
echo.

REM Check if we have src\api_server.py
if not exist "src\api_server.py" (
    if not exist "%~dp0src\api_server.py" (
        echo ERROR: Cannot find src\api_server.py
        echo Please ensure all server files are in the correct location.
        pause
        exit /b 1
    )
)

REM Strategy 1: Try common Python installation locations
echo [1/3] Searching for Python installation...
set PYTHON_CMD=
set PYTHON_FOUND=0

for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python38\python.exe"
    "%APPDATA%\Local\Programs\Python\Python313\python.exe"
    "%APPDATA%\Local\Programs\Python\Python312\python.exe"
    "%APPDATA%\Local\Programs\Python\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "python"
) do (
    %%~P --version >nul 2>&1
    if not errorlevel 1 (
        REM Verify Python works (not corrupted) - check for pip module
        %%~P -c "import sys; import pip" >nul 2>&1
        if not errorlevel 1 (
            set PYTHON_CMD=%%~P
            set PYTHON_FOUND=1
            echo Found working Python: %%~P
            goto :check_dependencies
        ) else (
            echo Skipping corrupted Python: %%~P
        )
    )
)

REM Strategy 2: Try to create a new virtual environment
echo.
echo No working Python found in standard locations.
echo Attempting to create local virtual environment...
echo.

REM Try to find ANY Python that can create a venv (even if pip is broken, venv might work)
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "python"
) do (
    echo Trying %%~P...
    %%~P -m venv "server_venv" >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=server_venv\Scripts\python.exe
        set PYTHON_FOUND=1
        echo ✓ Created virtual environment using %%~P
        goto :check_dependencies
    )
)

REM Strategy 3: Complete failure
echo.
echo ERROR: Could not find or create a working Python environment!
echo.
echo Solutions:
echo   1. Install Python 3.8 or higher from: https://www.python.org/downloads/
echo      IMPORTANT: Check "Add Python to PATH" during installation
echo.
echo   2. If Python is already installed, repair or reinstall it
echo.
echo   3. Contact your system administrator for assistance
echo.
pause
exit /b 1

:check_dependencies
echo [2/3] Checking dependencies...
%PYTHON_CMD% -c "import flask, flask_cors, sqlalchemy, waitress" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    echo   - Flask (web server)
    echo   - Flask-CORS (cross-origin support)
    echo   - SQLAlchemy (database)
    echo   - Waitress (production server)
    %PYTHON_CMD% -m pip install --quiet --disable-pip-version-check flask flask-cors sqlalchemy waitress
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
    echo All packages installed successfully!
) else (
    echo All dependencies available
)

echo.
echo [3/3] Starting API Server
echo ============================================================
echo.

%PYTHON_CMD% --version
echo.

echo Server will run on: http://0.0.0.0:5000
echo Other computers can connect using: http://YOUR-IP-ADDRESS:5000
echo.
echo To find your IP address, run: ipconfig
echo Look for "IPv4 Address" under your active network adapter
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

REM Start the server
%PYTHON_CMD% "%~dp0src\api_server.py"

echo.
echo Server stopped.
pause
