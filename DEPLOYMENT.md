# 📦 Deployment Guide - Alnoor Medical Services

Complete guide for building, packaging, and deploying the Alnoor Medical Services Tracking application.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Building the Executable](#building-the-executable)
- [Creating the Installer](#creating-the-installer)
- [Distribution](#distribution)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Development Environment
- **Python**: 3.10 or higher
- **Operating System**: Windows 10/11 (64-bit)
- **Virtual Environment**: Activated (`.venv`)

### Required Tools
1. **PyInstaller** (included in requirements.txt)
   ```powershell
   pip install PyInstaller>=6.0.0
   ```

2. **Inno Setup** (for Windows installer)
   - Download from: https://jrsoftware.org/isdl.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6`

### Verify Installation
```powershell
# Check Python version
python --version  # Should be 3.10+

# Check PyInstaller
pyinstaller --version  # Should be 6.0+

# Verify all dependencies
pip install -r requirements.txt
```

---

## Building the Executable

### Step 1: Clean Previous Builds
```powershell
# Remove old build artifacts
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path *.spec) { Remove-Item -Force *.spec }
```

### Step 2: Build Using Spec File
```powershell
# Build the executable
pyinstaller alnoor.spec

# This creates:
# - dist/AlnoorMedicalServices.exe (standalone executable)
# - build/ (temporary build files)
```

**Build Configuration:**
- **Mode**: One-file executable (all dependencies bundled)
- **Console**: Disabled (GUI application)
- **UPX Compression**: Enabled (reduces file size)
- **Icon**: `resources/icon.ico` (if available)

### Step 3: Test the Executable
```powershell
# Navigate to dist folder
cd dist

# Run the executable
.\AlnoorMedicalServices.exe

# Test key features:
# ✅ Application launches
# ✅ Database initializes
# ✅ All widgets load
# ✅ CRUD operations work
# ✅ Verification workflow functions
# ✅ Reports generate
# ✅ Backup/restore works
```

### Expected Output
- **File**: `dist/AlnoorMedicalServices.exe`
- **Size**: ~80-150 MB (includes Python runtime + all dependencies)
- **Runs**: Without Python installation required

---

## Build Options

### One-File vs One-Folder

**Current: One-File Mode (Default)**
- Single `.exe` file
- Slower startup (extracts to temp)
- Easier distribution
- ~80-150 MB

**Alternative: One-Folder Mode**
To switch to one-folder mode, uncomment the `COLLECT` section in `alnoor.spec`:
```python
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AlnoorMedicalServices',
)
```

Benefits:
- Faster startup
- Easier to debug
- Multiple files in folder

---

## Creating the Installer

### Option 1: Inno Setup (Recommended)

#### Step 1: Create Installer Script

Create `installer.iss`:
```iss
; Alnoor Medical Services Installer Script
#define MyAppName "Alnoor Medical Services"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Alnoor Medical Services"
#define MyAppExeName "AlnoorMedicalServices.exe"

[Setup]
AppId={{YOUR-GUID-HERE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=AlnoorMedicalServices_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=resources\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
```

#### Step 2: Compile Installer
```powershell
# Using Inno Setup compiler
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# Output: installer/AlnoorMedicalServices_Setup_v1.0.0.exe
```

### Option 2: Simple Batch Script

Create `build_and_package.bat`:
```batch
@echo off
echo ================================
echo Building Alnoor Medical Services
echo ================================

REM Clean previous builds
rmdir /s /q build dist 2>nul

REM Build executable
echo Building executable...
pyinstaller alnoor.spec

REM Check if build succeeded
if exist "dist\AlnoorMedicalServices.exe" (
    echo.
    echo ================================
    echo Build Successful!
    echo ================================
    echo Executable: dist\AlnoorMedicalServices.exe
    echo.
    
    REM Create distribution folder
    if not exist "release" mkdir release
    copy "dist\AlnoorMedicalServices.exe" "release\"
    
    echo Distribution package ready in: release\
) else (
    echo.
    echo Build FAILED!
    pause
)
```

---

## Distribution

### Package Contents

**Minimum Distribution:**
```
release/
├── AlnoorMedicalServices.exe     (Standalone executable)
└── README.txt                     (Quick start guide)
```

**Complete Distribution:**
```
release/
├── AlnoorMedicalServices.exe
├── README.txt
├── USER_MANUAL.pdf
├── CHANGELOG.md
└── data/                         (Optional: Sample database)
    └── alnoor.db
```

### Quick Start README

Create `release/README.txt`:
```
==============================================
Alnoor Medical Services - Tracking Application
Version 1.0.0
==============================================

QUICK START
-----------
1. Double-click AlnoorMedicalServices.exe
2. Application will create database automatically
3. Start adding products and tracking coupons

SYSTEM REQUIREMENTS
-------------------
- Windows 10/11 (64-bit)
- 4GB RAM (minimum)
- 100MB free disk space
- Screen resolution: 1280x720 or higher

FIRST RUN
---------
- Database is created in: %APPDATA%\Alnoor Medical Services\data\
- Backups saved to: %APPDATA%\Alnoor Medical Services\backups\

SUPPORT
-------
For questions or issues, contact:
support@alnoor-medical.example

DATABASE LOCATION
-----------------
User data: C:\Users\<YourName>\AppData\Local\Alnoor Medical Services\

BACKUP & RESTORE
----------------
Use File → Backup Database to create backups
Use File → Restore Database to restore from backup

==============================================
```

---

## Troubleshooting

### Common Build Issues

#### 1. Missing Modules Error
```
ModuleNotFoundError: No module named 'xxx'
```
**Solution:**
Add missing module to `hiddenimports` in `alnoor.spec`:
```python
hiddenimports=[
    'xxx',  # Add missing module
]
```

#### 2. DLL Not Found
```
Cannot find DLL: xxx.dll
```
**Solution:**
Check Python installation, reinstall PyQt6:
```powershell
pip uninstall PyQt6
pip install PyQt6
```

#### 3. Large File Size
**Solution:**
- Enable UPX compression (already enabled in spec)
- Exclude unnecessary modules in `excludes` section
- Consider one-folder mode for faster startup

#### 4. Slow Startup
**Solution:**
- Switch to one-folder mode (faster extraction)
- Add `--noupx` flag if UPX causing issues
- Check antivirus software (may scan on startup)

### Runtime Issues

#### 1. Database Not Created
**Check:**
- Write permissions in application directory
- Create `data` folder manually if needed
- Run as administrator

#### 2. Missing SQLite DLL
**Solution:**
Ensure SQLite is bundled:
```python
# In alnoor.spec, verify:
hiddenimports=['sqlalchemy.dialects.sqlite']
```

#### 3. PyQt6 Import Errors
**Solution:**
Rebuild with fresh virtual environment:
```powershell
python -m venv .venv_build
.venv_build\Scripts\activate
pip install -r requirements.txt
pyinstaller alnoor.spec
```

---

## Advanced Configuration

### Custom Icon
1. Create or obtain `.ico` file (256x256 recommended)
2. Save as `resources/icon.ico`
3. Rebuild with PyInstaller

### Version Information
Create `version_info.txt`:
```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Alnoor Medical Services'),
        StringStruct(u'FileDescription', u'Medical Services Tracking Application'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'ProductName', u'Alnoor Medical Services'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

Update `alnoor.spec`:
```python
exe = EXE(
    ...
    version_file='version_info.txt',
    ...
)
```

---

## Build Checklist

Before final distribution:

- [ ] All tests passing (`pytest tests/`)
- [ ] Executable builds without errors
- [ ] Application launches successfully
- [ ] Database initializes correctly
- [ ] All CRUD operations work
- [ ] Verification workflow functions
- [ ] Reports generate correctly
- [ ] Backup/restore works
- [ ] Icon displays properly
- [ ] Installer creates shortcuts
- [ ] Uninstaller works cleanly
- [ ] README.txt included
- [ ] Version number updated

---

## Performance Optimization

### Reduce File Size
```python
# In alnoor.spec, add to excludes:
excludes=[
    'tkinter',
    'matplotlib',
    'IPython',
    'notebook',
    'jupyter',
],
```

### Faster Startup
Use one-folder mode or optimize imports:
```python
# Lazy imports in code
def heavy_function():
    import pandas as pd  # Import only when needed
    ...
```

---

## Security Considerations

1. **Code Signing**: Consider signing executable for Windows SmartScreen
2. **Antivirus**: May flag PyInstaller executables (false positive)
3. **Database Encryption**: Consider encrypting sensitive CPR data
4. **Backup Security**: Encrypt backup files containing patient data

---

## Version Management

### Semantic Versioning
Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Example:
- `1.0.0` - Initial release
- `1.1.0` - Added CSV export
- `1.1.1` - Fixed validation bug

---

## Continuous Deployment

### Automated Build Script
Create `.github/workflows/build.yml` for CI/CD:
```yaml
name: Build Executable

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pyinstaller alnoor.spec
      - uses: actions/upload-artifact@v2
        with:
          name: AlnoorMedicalServices
          path: dist/AlnoorMedicalServices.exe
```

---

## Support & Maintenance

### Update Process
1. Develop and test changes
2. Update version number
3. Rebuild executable
4. Create new installer
5. Distribute to users
6. Update documentation

### User Data Migration
When upgrading, preserve user database:
```python
# In application code:
import shutil
old_db = 'data/alnoor.db'
backup_db = f'data/alnoor_v{OLD_VERSION}.db.bak'
shutil.copy2(old_db, backup_db)
```

---

## Contact & Support

**Developer**: Alnoor Medical Services Development Team
**Documentation**: See README.md and USER_MANUAL.md
**Issues**: Report bugs and feature requests

---

**Last Updated**: November 8, 2025
**Version**: 1.0.0
