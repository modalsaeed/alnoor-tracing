# Build Complete Distribution Package
# This script builds both the executable and the installer

param(
    [string]$Version = "1.0.0"
)

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    ALNOOR MEDICAL SERVICES - COMPLETE BUILD SCRIPT        " -ForegroundColor Cyan
Write-Host "    Version: $Version" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"
$startTime = Get-Date

# ============================================================================
# STEP 1: Environment Check
# ============================================================================
Write-Host "[1/5] Checking Environment..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

# Check Python
Write-Host "  Checking Python..." -NoNewline
try {
    $pythonPath = ".\venv\Scripts\python.exe"
    if (-not (Test-Path $pythonPath)) {
        throw "Python virtual environment not found"
    }
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Host " [OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host " [FAILED]" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    Write-Host "  Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Check PyInstaller
Write-Host "  Checking PyInstaller..." -NoNewline
try {
    $pyinstallerCheck = & $pythonPath -m PyInstaller --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [OK] $pyinstallerCheck" -ForegroundColor Green
    } else {
        throw "PyInstaller not installed"
    }
} catch {
    Write-Host " [NOT INSTALLED]" -ForegroundColor Red
    Write-Host "  Installing PyInstaller..." -ForegroundColor Yellow
    & $pythonPath -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Error: Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] PyInstaller installed" -ForegroundColor Green
}

# Check Inno Setup
Write-Host "  Checking Inno Setup..." -NoNewline
$isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $isccPath) {
    Write-Host " [OK] Found" -ForegroundColor Green
    $buildInstaller = $true
} else {
    Write-Host " [NOT FOUND]" -ForegroundColor Yellow
    Write-Host "    (Installer will not be built)" -ForegroundColor Yellow
    Write-Host "    Download from: https://jrsoftware.org/isdl.php" -ForegroundColor DarkGray
    $buildInstaller = $false
}

Write-Host ""

# ============================================================================
# STEP 2: Clean Previous Builds
# ============================================================================
Write-Host "[2/5] Cleaning Previous Builds..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

$cleanDirs = @("build", "dist")
foreach ($dir in $cleanDirs) {
    if (Test-Path $dir) {
        Write-Host "  Removing $dir..." -NoNewline
        Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
        Write-Host " [OK]" -ForegroundColor Green
    }
}

# Clean old installer
if (Test-Path "installer") {
    Write-Host "  Cleaning old installers..." -NoNewline
    Get-ChildItem "installer\*.exe" | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host " [OK]" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# STEP 3: Build Executable
# ============================================================================
Write-Host "[3/5] Building Executable..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

Write-Host "  Running PyInstaller..." -ForegroundColor Cyan
$buildStartTime = Get-Date

try {
    & $pythonPath -m PyInstaller alnoor.spec --clean --noconfirm
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed"
    }
} catch {
    Write-Host "  [BUILD FAILED]" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

$buildEndTime = Get-Date
$buildDuration = ($buildEndTime - $buildStartTime).TotalSeconds

# Verify executable exists
$exePath = "dist\AlnoorMedicalServices.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Host "  [OK] Executable built successfully" -ForegroundColor Green
    Write-Host "    Path: $exePath" -ForegroundColor DarkGray
    Write-Host "    Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor DarkGray
    Write-Host "    Time: $([math]::Round($buildDuration, 1))s" -ForegroundColor DarkGray
} else {
    Write-Host "  [EXECUTABLE NOT FOUND!]" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# STEP 4: Build Installer (if Inno Setup available)
# ============================================================================
if ($buildInstaller) {
    Write-Host "[4/5] Building Installer..." -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

    Write-Host "  Running Inno Setup Compiler..." -ForegroundColor Cyan
    $installerStartTime = Get-Date

    # Create installer directory if it doesn't exist
    if (-not (Test-Path "installer")) {
        New-Item -ItemType Directory -Path "installer" | Out-Null
    }

    try {
        & $isccPath installer.iss
        if ($LASTEXITCODE -ne 0) {
            throw "Inno Setup compilation failed"
        }
    } catch {
        Write-Host "  [INSTALLER BUILD FAILED]" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
        exit 1
    }

    $installerEndTime = Get-Date
    $installerDuration = ($installerEndTime - $installerStartTime).TotalSeconds

    # Verify installer exists
    $installerPath = "installer\AlnoorMedicalServices_Setup_v$Version.exe"
    if (Test-Path $installerPath) {
        $installerSize = (Get-Item $installerPath).Length / 1MB
        Write-Host "  [OK] Installer built successfully" -ForegroundColor Green
        Write-Host "    Path: $installerPath" -ForegroundColor DarkGray
        Write-Host "    Size: $([math]::Round($installerSize, 2)) MB" -ForegroundColor DarkGray
        Write-Host "    Time: $([math]::Round($installerDuration, 1))s" -ForegroundColor DarkGray
    } else {
        Write-Host "  [INSTALLER NOT FOUND!]" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
} else {
    Write-Host "[4/5] Building Installer..." -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  [SKIPPED] (Inno Setup not installed)" -ForegroundColor DarkGray
    Write-Host ""
}

# ============================================================================
# STEP 5: Generate Distribution Package
# ============================================================================
Write-Host "[5/5] Generating Distribution Package..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

# Create release directory
$releaseDir = "release\v$Version"
if (Test-Path $releaseDir) {
    Remove-Item -Recurse -Force $releaseDir
}
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null

# Copy files
Write-Host "  Copying files..." -NoNewline

$filesToCopy = @(
    @{Source = "dist\AlnoorMedicalServices.exe"; Dest = "$releaseDir\AlnoorMedicalServices.exe"},
    @{Source = "README.md"; Dest = "$releaseDir\README.md"}
)

if ($buildInstaller -and (Test-Path "installer\AlnoorMedicalServices_Setup_v$Version.exe")) {
    $filesToCopy += @{Source = "installer\AlnoorMedicalServices_Setup_v$Version.exe"; Dest = "$releaseDir\AlnoorMedicalServices_Setup_v$Version.exe"}
}

foreach ($file in $filesToCopy) {
    if (Test-Path $file.Source) {
        Copy-Item $file.Source $file.Dest -Force
    }
}

Write-Host " [OK]" -ForegroundColor Green

# Generate checksums
Write-Host "  Generating checksums..." -NoNewline
$checksumPath = "$releaseDir\CHECKSUMS.txt"
$checksumContent = "SHA256 Checksums for Alnoor Medical Services v$Version`n"
$checksumContent += "=" * 70 + "`n`n"

Get-ChildItem "$releaseDir\*.exe" | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    $checksumContent += "$($_.Name):`n  $hash`n`n"
}

$checksumContent | Out-File $checksumPath -Encoding UTF8
Write-Host " [OK]" -ForegroundColor Green

# Create release notes
Write-Host "  Creating release notes..." -NoNewline
$releaseNotesPath = "$releaseDir\RELEASE_NOTES.txt"
$releaseNotes = @"
Alnoor Medical Services - Version $Version
=========================================

Release Date: $(Get-Date -Format "MMMM d, yyyy")
Build Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

INSTALLATION OPTIONS
--------------------

Option 1: Windows Installer (Recommended)
   - Run: AlnoorMedicalServices_Setup_v$Version.exe
   - Follow installation wizard
   - Creates desktop and start menu shortcuts
   - Sets up application data folders
   - Includes uninstaller

Option 2: Portable Executable
   - Run: AlnoorMedicalServices.exe
   - No installation required
   - Data stored in application folder

FEATURES
--------

Product Management
   - Add, edit, delete medical products
   - Track stock levels in real-time
   - Product categories and descriptions

Purchase Orders
   - Record incoming stock shipments
   - FIFO (First In, First Out) tracking
   - Automatic stock updates

Patient Coupons
   - Manage patient distributions
   - Batch verification workflow
   - Multi-coupon selection (Ctrl+Click)
   - Manual verification reference entry
   - Stock deduction with FIFO

Medical Centres
   - Track distribution locations
   - Associate coupons with centres

Reports & Analytics
   - Real-time stock reports
   - FIFO stock usage analysis
   - Activity audit log
   - Export to Excel/CSV

SYSTEM REQUIREMENTS
-------------------

- Windows 10 (64-bit) or later
- 2 GB RAM (4 GB recommended)
- 200 MB free space
- 1280x720 minimum resolution

VERIFICATION
------------

See CHECKSUMS.txt for SHA256 hashes to verify file integrity.

Copyright (C) 2025 Alnoor Medical Services
"@

$releaseNotes | Out-File $releaseNotesPath -Encoding UTF8
Write-Host " [OK]" -ForegroundColor Green

Write-Host ""

# ============================================================================
# SUMMARY
# ============================================================================
$endTime = Get-Date
$totalDuration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "                BUILD COMPLETED SUCCESSFULLY!              " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Distribution Package:" -ForegroundColor Cyan
Write-Host "   $releaseDir" -ForegroundColor White
Write-Host ""

Write-Host "Files Created:" -ForegroundColor Cyan
Get-ChildItem $releaseDir -Recurse -File | ForEach-Object {
    $size = $_.Length / 1MB
    $sizeStr = if ($size -gt 1) { "$([math]::Round($size, 2)) MB" } else { "$([math]::Round($_.Length / 1KB, 2)) KB" }
    Write-Host ("   {0,-45} {1,10}" -f $_.Name, $sizeStr) -ForegroundColor White
}

Write-Host ""
Write-Host "Total Build Time: $([math]::Round($totalDuration, 1)) seconds" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Test the installer on a clean Windows machine" -ForegroundColor White
Write-Host "   2. Create GitHub Release with the installer" -ForegroundColor White
Write-Host "   3. Share download link with users" -ForegroundColor White
Write-Host ""

# Open release folder
$openFolder = Read-Host "Open release folder? (Y/n)"
if ($openFolder -ne "n" -and $openFolder -ne "N") {
    Start-Process explorer.exe $releaseDir
}

Write-Host ""
Write-Host "BUILD COMPLETE!" -ForegroundColor Green
Write-Host ""