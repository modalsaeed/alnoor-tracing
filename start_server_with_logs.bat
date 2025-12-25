@echo off
REM Start Alnoor API Server with comprehensive logging enabled

echo ============================================================
echo Starting Alnoor API Server with LOGGING ENABLED
echo ============================================================
echo.

REM Set environment variable to enable logging
set ALNOOR_ENABLE_LOGGING=true

REM Navigate to script directory
cd /d "%~dp0"

REM Start server with logging
echo Starting server...
echo Logs will be saved to: logs\api_server_YYYYMMDD.log
echo.
python src\api_server.py

pause
