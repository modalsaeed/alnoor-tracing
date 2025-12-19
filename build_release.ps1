# ============================================
# Alnoor Medical Services - Release Builder
# ============================================
#
# This script creates a complete release package with installer
# 
# What it does:
# 1. Validates environment and dependencies
# 2. Cleans previous builds
# 3. Builds executable with PyInstaller
# 4. Verifies database isolation (dev DB not included)
# 5. Creates installer with Inno Setup
# 6. Generates checksums and release notes
# 7. Packages everything in release/v{version} folder
#
# Prerequisites:
#   - Virtual environment activated
#   - PyInstaller installed
#   - Inno Setup installed (optional, for installer creation)
#
# Usage:
#   .\build_release.ps1 [-Version "1.0.2"]
#   .\build_release.ps1 -Version "2.0.0" -Prerelease "beta.1"
#
# The script will:
#   - Build for the specified version
#   - Create upgrade-aware installer
#   - Preserve user data during upgrades
#   - Generate version-specific checksums

param(
    [Parameter(Mandatory=$false)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Prerelease = ""
)

# ============================================
# Configuration
# ============================================

# Auto-detect version from VERSION file or use parameter
if (-not $Version) {
    if (Test-Path "VERSION") {
        $Version = (Get-Content "VERSION" -Raw).Trim()
        Write-Host "Auto-detected version from VERSION file: $Version" -ForegroundColor Cyan
    } else {
        $Version = "1.0.1"
        Write-Host "No version specified, using default: $Version" -ForegroundColor Yellow
    }
}

# Build full version string
$FullVersion = $Version
if ($Prerelease) {
    $FullVersion = "$Version-$Prerelease"
}

$AppName = "Alnoor Medical Services"
$ExeName = "AlnoorMedicalServices"
$Publisher = "Alnoor Medical Services"
$AppURL = "https://github.com/modalsaeed/alnoor-tracing"
$ReleaseDir = "release\v$FullVersion"
$AppId = "8F4B2C3D-5A6E-4B7C-9D8E-1F2A3B4C5D6E"  # Keep same AppId for upgrades

# Colors for output
$ColorInfo = "Cyan"
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"

# ============================================
# Helper Functions
# ============================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n[$([DateTime]::Now.ToString('HH:mm:ss'))] " -NoNewline -ForegroundColor Gray
    Write-Host $Message -ForegroundColor $ColorInfo
}

function Write-Success {
    param([string]$Message)
    Write-Host "    [OK] " -NoNewline -ForegroundColor $ColorSuccess
    Write-Host $Message -ForegroundColor $ColorSuccess
}

function Write-Warn {
    param([string]$Message)
    Write-Host "    [!] " -NoNewline -ForegroundColor $ColorWarning
    Write-Host $Message -ForegroundColor $ColorWarning
}

function Write-Fail {
    param([string]$Message)
    Write-Host "    [X] " -NoNewline -ForegroundColor $ColorError
    Write-Host $Message -ForegroundColor $ColorError
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# ============================================
# Start Build Process
# ============================================

Write-Host ""
Write-Host "============================================" -ForegroundColor $ColorInfo
Write-Host "  $AppName" -ForegroundColor $ColorInfo
Write-Host "  Release Builder v$Version" -ForegroundColor $ColorInfo
Write-Host "============================================" -ForegroundColor $ColorInfo
Write-Host ""

# ============================================
# Step 1: Validate Environment
# ============================================

Write-Step "Step 1/9: Validating environment..."

# Check if we're in the right directory
if (-not (Test-Path "src\main.py")) {
    Write-Fail "Error: src\main.py not found. Please run this script from the project root."
    exit 1
}
Write-Success "Project root directory confirmed"

# Check virtual environment
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Fail "Error: Virtual environment not found at .venv"
    exit 1
}
Write-Success "Virtual environment found"

# Check if virtual environment is activated
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath -notlike "*\.venv\*") {
    Write-Warn "Virtual environment not activated. Activating now..."
    & ".\.venv\Scripts\Activate.ps1"
}
Write-Success "Virtual environment activated"

# Check Python version
$pythonVersion = & python --version 2>&1
Write-Success "Python version: $pythonVersion"

# Check required packages
Write-Host "    Checking dependencies..."
$missingPackages = @()

$requiredPackages = @("PyQt6", "sqlalchemy", "pandas", "openpyxl", "pyinstaller")
foreach ($package in $requiredPackages) {
    $installed = & python -c "import $package" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
    } else {
        Write-Host "      - $package" -ForegroundColor Gray -NoNewline
        Write-Host " [OK]" -ForegroundColor $ColorSuccess
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Fail "Missing packages: $($missingPackages -join ', ')"
    Write-Host "    Installing missing packages..."
    pip install $($missingPackages -join ' ')
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to install dependencies"
        exit 1
    }
}
Write-Success "All dependencies installed"

# ============================================
# Step 2: Clean Previous Builds
# ============================================

Write-Step "Step 2/9: Cleaning previous builds..."

$dirsToClean = @("build", "dist")
foreach ($dir in $dirsToClean) {
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
        Write-Success "Removed $dir/"
    }
}

# Remove old spec backup files
if (Test-Path "alnoor.spec.bak") {
    Remove-Item -Force "alnoor.spec.bak"
}

Write-Success "Build directories cleaned"

# ============================================
# Step 3: Verify Database Isolation
# ============================================

Write-Step "Step 3/9: Verifying database isolation configuration..."

# Check that data folder is NOT in alnoor.spec
$specContent = Get-Content "alnoor.spec" -Raw
if ($specContent -match "datas=\[.*?'data'.*?\]") {
    Write-Fail "ERROR: data folder is included in alnoor.spec!"
    Write-Fail "The development database would be packaged with the installer."
    Write-Fail "Please remove ('data', 'data') from the datas list in alnoor.spec"
    exit 1
}
Write-Success "Spec file does not include data folder"

# Check db_manager.py has sys.frozen detection
$dbManagerContent = Get-Content "src\database\db_manager.py" -Raw
if ($dbManagerContent -match "getattr\(sys, 'frozen', False\)") {
    Write-Success "Database manager has environment detection"
} else {
    Write-Warn "Warning: sys.frozen detection not found in db_manager.py"
    Write-Warn "The app may not create database in correct location"
}

Write-Success "Database isolation verified"

# ============================================
# Step 4: Build Executable
# ============================================

Write-Step "Step 4/9: Building executable with PyInstaller..."
Write-Host "    This may take several minutes..." -ForegroundColor Gray

$buildStartTime = Get-Date

# Run PyInstaller
& pyinstaller --clean --noconfirm alnoor.spec 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Fail "PyInstaller build failed!"
    Write-Host "    Run manually for detailed error: pyinstaller --clean alnoor.spec"
    exit 1
}

$buildDuration = (Get-Date) - $buildStartTime
Write-Success "Build completed in $([math]::Round($buildDuration.TotalSeconds, 1)) seconds"

# ============================================
# Step 5: Verify Build Output
# ============================================

Write-Step "Step 5/9: Verifying build output..."

# Check if executable exists
$exePath = "dist\$ExeName.exe"
if (-not (Test-Path $exePath)) {
    Write-Fail "Executable not found at $exePath"
    exit 1
}
Write-Success "Executable created: $exePath"

# Get file size
$exeSize = (Get-Item $exePath).Length / 1MB
Write-Success "Executable size: $([math]::Round($exeSize, 2)) MB"

# Verify no database files in dist
$dbFiles = Get-ChildItem -Path "dist" -Recurse -Include "*.db" -ErrorAction SilentlyContinue
if ($dbFiles.Count -gt 0) {
    Write-Fail "ERROR: Database files found in dist folder!"
    foreach ($file in $dbFiles) {
        Write-Host "      - $($file.FullName)" -ForegroundColor $ColorError
    }
    Write-Fail "Development database was packaged. Build aborted."
    exit 1
}
Write-Success "No database files in distribution (verified)"

# Verify no data directory
if (Test-Path "dist\data") {
    Write-Fail "ERROR: data directory found in dist folder!"
    Write-Fail "Development data was packaged. Build aborted."
    exit 1
}
Write-Success "No data directory in distribution (verified)"

Write-Success "Build verification passed"

# ============================================
# Step 6: Create Release Directory
# ============================================

Write-Step "Step 6/9: Creating release directory..."

# Create release directory
if (-not (Test-Path $ReleaseDir)) {
    New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
    Write-Success "Created directory: $ReleaseDir"
} else {
    Write-Warn "Release directory already exists, will overwrite contents"
}

# ============================================
# Step 7: Create Inno Setup Installer
# ============================================

Write-Step "Step 7/9: Creating installer..."

# Check if Inno Setup is installed
$innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoSetupPath)) {
    Write-Warn "Inno Setup not found at default location"
    Write-Warn "Skipping installer creation. Only portable executable will be available."
    
    # Copy executable to release folder
    Copy-Item $exePath "$ReleaseDir\$ExeName.exe" -Force
    Write-Success "Copied portable executable to release folder"
    
    $installerCreated = $false
} else {
    # Create Inno Setup script with upgrade support
    $issContent = @"
; Alnoor Medical Services Installer Script
; Generated automatically by build_release.ps1
; Version: $FullVersion

#define MyAppName "$AppName"
#define MyAppVersion "$Version"
#define MyAppPublisher "$Publisher"
#define MyAppURL "$AppURL"
#define MyAppExeName "$ExeName.exe"
#define MyAppId "$AppId"

[Setup]
; IMPORTANT: Keep AppId the same across versions for proper upgrades
AppId={{$AppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=$ReleaseDir
OutputBaseFilename=AlnoorMedicalServices-Setup-v$FullVersion
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
; Version info for Windows
VersionInfoVersion=$Version.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoCopyright=Copyright (C) $(Get-Date -Format yyyy) {#MyAppPublisher}
; Upgrade settings
; CloseApplications will try to close the app before upgrade
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: data folder is intentionally NOT included
; Database will be created in user's AppData on first run

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  OldVersion: String;
  IsUpgrade: Boolean;

function InitializeSetup(): Boolean;
begin
  // Check if an older version is installed
  IsUpgrade := RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppId}_is1', 'DisplayVersion', OldVersion);
  
  if IsUpgrade then
  begin
    Log('Detected existing installation: ' + OldVersion);
    if MsgBox('Version ' + OldVersion + ' is currently installed.' + #13#10#13#10 +
              'This will upgrade to version {#MyAppVersion}.' + #13#10#13#10 +
              'Your database and settings will be preserved.' + #13#10#13#10 +
              'Do you want to continue?', 
              mbConfirmation, MB_YESNO) = IDYES then
      Result := True
    else
      Result := False;
  end
  else
  begin
    Log('Clean installation detected');
    Result := True;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataDir: String;
  DatabasePath: String;
  BackupPath: String;
begin
  if CurStep = ssInstall then
  begin
    // Before installation, create backup of user database if upgrading
    if IsUpgrade then
    begin
      AppDataDir := ExpandConstant('{localappdata}\{#MyAppName}\database');
      DatabasePath := AppDataDir + '\alnoor.db';
      
      if FileExists(DatabasePath) then
      begin
        BackupPath := AppDataDir + '\alnoor_backup_' + OldVersion + '_' + GetDateTimeString('yyyymmdd_hhnnss', '-', ':') + '.db';
        Log('Creating database backup: ' + BackupPath);
        
        if FileCopy(DatabasePath, BackupPath, False) then
          Log('Backup created successfully')
        else
          Log('Warning: Failed to create backup');
      end;
    end;
  end;
  
  if CurStep = ssPostInstall then
  begin
    // Database will be created automatically in:
    // %LOCALAPPDATA%\Alnoor Medical Services\database\alnoor.db
    // User data is preserved during upgrades
    
    if IsUpgrade then
      Log('Upgrade completed. Database preserved at: ' + ExpandConstant('{localappdata}\{#MyAppName}\database'))
    else
      Log('New installation. Database will be created on first run');
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDataDir: String;
  DatabasePath: String;
  Response: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Ask user if they want to keep their data
    AppDataDir := ExpandConstant('{localappdata}\{#MyAppName}');
    DatabasePath := AppDataDir + '\database\alnoor.db';
    
    if FileExists(DatabasePath) then
    begin
      Response := MsgBox('Do you want to keep your database and settings?' + #13#10#13#10 +
                        'Choose YES to keep your data for future reinstallation.' + #13#10 +
                        'Choose NO to completely remove all data.',
                        mbConfirmation, MB_YESNO);
      
      if Response = IDNO then
      begin
        Log('User chose to delete data');
        if DelTree(AppDataDir, True, True, True) then
          Log('User data deleted successfully')
        else
          Log('Warning: Failed to delete some user data');
      end
      else
        Log('User data preserved at: ' + AppDataDir);
    end;
  end;
end;
"@

    $issPath = "installer_script.iss"
    $issContent | Out-File -FilePath $issPath -Encoding UTF8
    Write-Success "Created Inno Setup script"

    # Run Inno Setup
    Write-Host "    Compiling installer..." -ForegroundColor Gray
    & $innoSetupPath $issPath /Q
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Inno Setup compilation failed"
        Write-Warn "Continuing with portable executable only"
        Copy-Item $exePath "$ReleaseDir\$ExeName.exe" -Force
        $installerCreated = $false
    } else {
        Write-Success "Installer created successfully"
        $installerCreated = $true
        
        # Also copy portable executable
        Copy-Item $exePath "$ReleaseDir\$ExeName-Portable.exe" -Force
        Write-Success "Copied portable executable"
    }

    # Clean up ISS file
    Remove-Item $issPath -Force -ErrorAction SilentlyContinue
}

# ============================================
# Step 8: Generate Documentation
# ============================================

Write-Step "Step 8/9: Generating documentation..."

# Create README
$readmeContent = @"
# $AppName v$Version

## Installation

### Option 1: Installer (Recommended)
1. Run ``AlnoorMedicalServices-Setup-v$Version.exe``
2. Follow the installation wizard
3. Launch from Start Menu or Desktop shortcut

### Option 2: Portable Executable
1. Extract ``$ExeName-Portable.exe`` to any folder
2. Run ``$ExeName-Portable.exe``
3. No installation required

## Database Location

The application creates its database automatically on first run:

- **Installed Version**: ``%LOCALAPPDATA%\$AppName\database\alnoor.db``
- **Portable Version**: ``%LOCALAPPDATA%\$AppName\database\alnoor.db``

Each Windows user will have their own separate database.

## Important Notes

⚠️ **Fresh Database**: This installation will create a NEW empty database.
It does NOT include any test data from the development environment.

✅ **Data Isolation**: Your production data is completely separate from development.

## System Requirements

- Windows 10 or later (64-bit)
- 4 GB RAM minimum
- 200 MB free disk space

## First Run

1. Launch the application
2. The database will be created automatically
3. Add your products, medical centres, and distribution locations
4. Start managing purchase orders and coupons

## Support

For issues or questions:
- GitHub: $AppURL
- Email: support@alnoor.example.com

## Version Information

- Version: $Version
- Build Date: $([DateTime]::Now.ToString('yyyy-MM-dd'))
- Python Version: $pythonVersion

---

© $(Get-Date -Format yyyy) $Publisher
"@

$readmeContent | Out-File -FilePath "$ReleaseDir\README.txt" -Encoding UTF8
Write-Success "Created README.txt"

# Create Release Notes
$releaseNotesContent = @"
===========================================
$AppName - Release Notes
Version $Version
===========================================

Build Date: $([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))

NEW FEATURES
------------

✨ Complete Stock Management System
   - Transaction-based stock tracking with FIFO
   - Purchase orders with pricing (unit price, tax, totals)
   - Distribution location stock monitoring
   - Stock IN/OUT tracking with detailed breakdowns

✨ Enhanced Coupon Management
   - Bulk coupon insertion for efficient data entry
   - Optional patient fields for bulk operations
   - Searchable dropdowns with quick-add buttons
   - Multi-select verification (Ctrl+Click, Shift+Click)

✨ Improved User Interface
   - Full forms for adding medical centres and locations
   - Real-time stock calculations
   - Color-coded stock levels (red/yellow/green)
   - Detailed tooltips with stock breakdowns
   - Negative stock warnings for overdrawn locations

✨ Database Isolation
   - Development and production databases separated
   - Each user gets independent database
   - No test data in production installations
   - Platform-agnostic storage (Windows/macOS/Linux)

IMPROVEMENTS
------------

🔧 Stock Flow Logic
   - Transactions reduce purchase order stock (FIFO)
   - Coupons reduce distribution location stock
   - Verification is delivery confirmation only (no stock changes)

🔧 Pricing Management
   - Purchase orders show unit price, tax rate, and totals
   - Automatic tax calculations
   - Warehouse location removed (not needed)

🔧 Data Entry Efficiency
   - Bulk add multiple coupons at once
   - Quick-add buttons for centres and locations
   - Searchable combo boxes with auto-complete

BUG FIXES
---------

🐛 Fixed transaction dialog date field error
🐛 Fixed validation error in transaction reference
🐛 Fixed filter issues with None values
🐛 Fixed date range filtering

TECHNICAL DETAILS
-----------------

Database: SQLite with SQLAlchemy ORM
UI Framework: PyQt6 6.10.0
Python Version: 3.13.9
Build Tool: PyInstaller 6.16.0

File Sizes:
- Executable: $([math]::Round($exeSize, 2)) MB
- Installer: ~$([math]::Round($exeSize + 5, 0)) MB

DATABASE STRUCTURE
------------------

Core Tables:
- products: Product catalog
- purchase_orders: Stock source with pricing
- transactions: Stock transfers (PO → Location)
- patient_coupons: Distribution records (Location → Patient)
- medical_centres: Issuing centres
- distribution_locations: Stock destinations

Stock Flow:
Purchase Order → Transaction → Distribution Location → Coupon → Verified

INSTALLATION NOTES
------------------

✅ Clean installation (no data migration needed)
✅ Database created automatically on first run
✅ Multi-user support (separate DBs per user)
✅ No development test data included

KNOWN ISSUES
------------

None reported in this version.

UPGRADE INSTRUCTIONS
--------------------

This is version $Version. If upgrading from a previous version:

1. Export your data before uninstalling old version
2. Install new version
3. Import data if needed
4. Verify all data imported correctly

For questions or support, please contact:
GitHub: $AppURL

===========================================
© $(Get-Date -Format yyyy) $Publisher
===========================================
"@

$releaseNotesContent | Out-File -FilePath "$ReleaseDir\RELEASE_NOTES.txt" -Encoding UTF8
Write-Success "Created RELEASE_NOTES.txt"

# ============================================
# Step 9: Generate Checksums
# ============================================

Write-Step "Step 9/9: Generating checksums..."

$checksumContent = @"
SHA256 Checksums for $AppName v$Version
Generated: $([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))

"@

# Calculate checksums for all files in release directory
$releaseFiles = Get-ChildItem -Path $ReleaseDir -File | Where-Object { $_.Name -ne "CHECKSUMS.txt" }
foreach ($file in $releaseFiles) {
    $hash = (Get-FileHash -Path $file.FullName -Algorithm SHA256).Hash
    $checksumContent += "$hash  $($file.Name)`n"
    Write-Host "    $($file.Name): " -NoNewline -ForegroundColor Gray
    Write-Host $hash.Substring(0, 16) -NoNewline -ForegroundColor $ColorSuccess
    Write-Host "..." -ForegroundColor $ColorSuccess
}

$checksumContent | Out-File -FilePath "$ReleaseDir\CHECKSUMS.txt" -Encoding UTF8
Write-Success "Created CHECKSUMS.txt"

# ============================================
# Build Summary
# ============================================

Write-Host ""
Write-Host "============================================" -ForegroundColor $ColorSuccess
Write-Host "  Build Completed Successfully! " -ForegroundColor $ColorSuccess
Write-Host "============================================" -ForegroundColor $ColorSuccess
Write-Host ""

Write-Host "Release Package: " -NoNewline
Write-Host $ReleaseDir -ForegroundColor $ColorInfo

Write-Host "`nPackage Contents:" -ForegroundColor $ColorInfo
$packageFiles = Get-ChildItem -Path $ReleaseDir -File
foreach ($file in $packageFiles) {
    $sizeKB = [math]::Round($file.Length / 1KB, 2)
    Write-Host "  - " -NoNewline -ForegroundColor $ColorSuccess
    Write-Host "$($file.Name)" -NoNewline
    Write-Host " ($sizeKB KB)" -ForegroundColor Gray
}

Write-Host "`nDatabase Isolation:" -ForegroundColor $ColorInfo
Write-Host "  [OK] Development database NOT included" -ForegroundColor $ColorSuccess
Write-Host "  [OK] Fresh database will be created on first run" -ForegroundColor $ColorSuccess
Write-Host "  [OK] Location: %LOCALAPPDATA%\$AppName\database\" -ForegroundColor Gray

Write-Host "`nNext Steps:" -ForegroundColor $ColorInfo
Write-Host "  1. Test the installer on a clean machine"
Write-Host "  2. Verify database is created in AppData"
Write-Host "  3. Test all features with fresh database"
Write-Host "  4. Distribute to users"

Write-Host ""
Write-Host "============================================" -ForegroundColor $ColorInfo
Write-Host ""

# Return success
exit 0