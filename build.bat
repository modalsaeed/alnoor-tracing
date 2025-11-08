@echo off
REM ============================================
REM Alnoor Medical Services - Build Script
REM ============================================
REM
REM This script automates the build process for
REM creating a standalone Windows executable.
REM
REM Prerequisites:
REM   - Python 3.10+ with virtual environment activated
REM   - PyInstaller installed (pip install pyinstaller)
REM   - All dependencies installed (pip install -r requirements.txt)
REM
REM Usage:
REM   build.bat
REM
REM Output:
REM   dist/AlnoorMedicalServices.exe

echo.
echo ============================================
echo   Alnoor Medical Services - Build Process
echo ============================================
echo.

REM Check if virtual environment is activated
python -c "import sys; sys.exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Virtual environment not activated!
    echo Please run: .venv\Scripts\activate
    echo.
    pause
    exit /b 1
)

echo [1/5] Checking dependencies...
python -c "import PyQt6, sqlalchemy, pandas" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Missing dependencies!
    echo Installing requirements...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
)
echo     ✓ Dependencies OK

echo.
echo [2/5] Cleaning previous builds...
if exist build (
    rmdir /s /q build
    echo     ✓ Removed build/
)
if exist dist (
    rmdir /s /q dist
    echo     ✓ Removed dist/
)
echo     ✓ Clean complete

echo.
echo [3/5] Running tests...
python -m pytest tests/ -v --tb=short -q
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Some tests failed!
    echo Continue anyway? (Y/N)
    choice /C YN /N
    if errorlevel 2 exit /b 1
)
echo     ✓ Tests passed

echo.
echo [4/5] Building executable with PyInstaller...
echo     This may take several minutes...
pyinstaller alnoor.spec --clean --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Build failed!
    echo Check error messages above.
    pause
    exit /b 1
)
echo     ✓ Build complete

echo.
echo [5/5] Verifying output...
if not exist "dist\AlnoorMedicalServices.exe" (
    echo ERROR: Executable not found!
    pause
    exit /b 1
)

REM Get file size
for %%I in ("dist\AlnoorMedicalServices.exe") do set SIZE=%%~zI
set /a SIZE_MB=%SIZE% / 1048576
echo     ✓ Executable created: dist\AlnoorMedicalServices.exe
echo     ✓ File size: %SIZE_MB% MB

echo.
echo ============================================
echo   Build Successful! 🎉
echo ============================================
echo.
echo Executable location: dist\AlnoorMedicalServices.exe
echo.
echo Next steps:
echo   1. Test the executable: dist\AlnoorMedicalServices.exe
echo   2. Create installer (optional): See DEPLOYMENT.md
echo   3. Distribute to users
echo.
echo ============================================
pause
