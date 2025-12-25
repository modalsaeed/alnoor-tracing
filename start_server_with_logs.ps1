# Start Alnoor API Server with comprehensive logging enabled

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting Alnoor API Server with LOGGING ENABLED" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variable to enable logging
$env:ALNOOR_ENABLE_LOGGING = "true"

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run from project root directory." -ForegroundColor Red
    pause
    exit 1
}

# Start server with logging
Write-Host "Starting server..." -ForegroundColor Green
Write-Host "Logs will be saved to: logs\api_server_YYYYMMDD.log" -ForegroundColor Yellow
Write-Host ""

.venv\Scripts\python.exe src\api_server.py
