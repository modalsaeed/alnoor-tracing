# ============================================
# Alnoor Medical Services - Build Script (PowerShell)
# ============================================
#
# This script automates the build process for
# creating a standalone Windows executable.
#
# Prerequisites:
#   - Python 3.10+ with virtual environment activated
#   - PyInstaller installed (pip install pyinstaller)
#   - All dependencies installed (pip install -r requirements.txt)
#
# Usage:
#   .\build.ps1
#
# Output:
#   dist/AlnoorMedicalServices.exe

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Alnoor Medical Services - Build Process" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
$venvActive = python -c "import sys; print(hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))" 2>&1
if ($venvActive -ne "True") {
    Write-Host "ERROR: Virtual environment not activated!" -ForegroundColor Red
    Write-Host "Please run: .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/5] Checking dependencies..." -ForegroundColor Yellow
$depCheck = python -c "import PyQt6, sqlalchemy, pandas" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "    Missing dependencies! Installing..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    ERROR: Failed to install dependencies!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host "    ✓ Dependencies OK" -ForegroundColor Green

Write-Host ""
Write-Host "[2/5] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "    ✓ Removed build/" -ForegroundColor Green
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "    ✓ Removed dist/" -ForegroundColor Green
}
Write-Host "    ✓ Clean complete" -ForegroundColor Green

Write-Host ""
Write-Host "[3/5] Running tests..." -ForegroundColor Yellow
python -m pytest tests/ -q --tb=line
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Some tests failed!" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        exit 1
    }
}
Write-Host "    ✓ Tests passed" -ForegroundColor Green

Write-Host ""
Write-Host "[4/5] Building executable with PyInstaller..." -ForegroundColor Yellow
Write-Host "    This may take several minutes..." -ForegroundColor Gray
pyinstaller alnoor.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    Write-Host "Check error messages above." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "    ✓ Build complete" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] Verifying output..." -ForegroundColor Yellow
if (-not (Test-Path "dist\AlnoorMedicalServices.exe")) {
    Write-Host "    ERROR: Executable not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Get file size
$fileSize = (Get-Item "dist\AlnoorMedicalServices.exe").Length
$fileSizeMB = [math]::Round($fileSize / 1MB, 2)
Write-Host "    ✓ Executable created: dist\AlnoorMedicalServices.exe" -ForegroundColor Green
Write-Host "    ✓ File size: $fileSizeMB MB" -ForegroundColor Green

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Build Successful! 🎉" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Executable location: " -NoNewline
Write-Host "dist\AlnoorMedicalServices.exe" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test the executable: dist\AlnoorMedicalServices.exe"
Write-Host "  2. Create installer (optional): See DEPLOYMENT.md"
Write-Host "  3. Distribute to users"
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
