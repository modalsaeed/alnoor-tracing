"""
Build script for creating Windows installer for Alnoor Medical Services.

This script mirrors the functionality of build_release.ps1 but in Python.
It creates a complete release package with installer.

What it does:
1. Validates environment and dependencies
2. Cleans previous builds
3. Builds executable with PyInstaller
4. Verifies database isolation (dev DB not included)
5. Creates installer with Inno Setup
6. Generates checksums and release notes
7. Packages everything in release/v{version} folder

Prerequisites:
  - Virtual environment activated
  - PyInstaller installed
  - Inno Setup installed (optional, for installer creation)

Usage:
  python build_installer.py [--version 1.0.2]
  python build_installer.py --version 2.0.0 --prerelease beta.1
"""

import os
import sys
import subprocess
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# ============================================
# Configuration
# ============================================

APP_NAME = "Alnoor Medical Services"
APP_AUTHOR = "Alnoor Medical Services"
APP_URL = "https://github.com/modalsaeed/alnoor-tracing"
EXECUTABLE_NAME = "AlnoorMedicalServices"
APP_ID = "8F4B2C3D-5A6E-4B7C-9D8E-1F2A3B4C5D6E"  # Keep same for upgrades

# Colors for terminal output
class Colors:
    INFO = '\033[96m'      # Cyan
    SUCCESS = '\033[92m'   # Green
    WARNING = '\033[93m'   # Yellow
    ERROR = '\033[91m'     # Red
    GRAY = '\033[90m'      # Gray
    RESET = '\033[0m'      # Reset
    BOLD = '\033[1m'       # Bold


# ============================================
# Helper Functions
# ============================================

def print_step(message):
    """Print a step header."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{Colors.GRAY}{timestamp}{Colors.RESET}] {Colors.INFO}{message}{Colors.RESET}")

def print_success(message):
    """Print a success message."""
    print(f"    {Colors.SUCCESS}[OK]{Colors.RESET} {Colors.SUCCESS}{message}{Colors.RESET}")

def print_warning(message):
    """Print a warning message."""
    print(f"    {Colors.WARNING}[!]{Colors.RESET} {Colors.WARNING}{message}{Colors.RESET}")

def print_error(message):
    """Print an error message."""
    print(f"    {Colors.ERROR}[X]{Colors.RESET} {Colors.ERROR}{message}{Colors.RESET}")

def check_command(command):
    """Check if a command exists."""
    return shutil.which(command) is not None

def auto_detect_version():
    """Auto-detect version from VERSION file or default to 1.0.1."""
    if Path("VERSION").exists():
        version = Path("VERSION").read_text().strip()
        print(f"{Colors.INFO}Auto-detected version from VERSION file: {version}{Colors.RESET}")
        return version
    else:
        version = "1.0.1"
        print(f"{Colors.WARNING}No version specified, using default: {version}{Colors.RESET}")
        return version

def calculate_sha256(filepath):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# ============================================
# Build Steps
# ============================================

def validate_environment():
    """Step 1: Validate environment."""
    print_step("Step 1/9: Validating environment...")
    
    # Check project root
    if not Path("src/main.py").exists():
        print_error("Error: src/main.py not found. Please run from project root.")
        return False
    print_success("Project root directory confirmed")
    
    # Check virtual environment
    if not Path(".venv/Scripts/python.exe").exists():
        print_error("Error: Virtual environment not found at .venv")
        return False
    print_success("Virtual environment found")
    
    # Get Python version
    result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
    python_version = result.stdout.strip() or result.stderr.strip()
    print_success(f"Python version: {python_version}")
    
    # Check required packages
    print(f"    {Colors.GRAY}Checking dependencies...{Colors.RESET}")
    # Map package names to their import names (some differ)
    required_packages = {
        "PyQt6": "PyQt6",
        "sqlalchemy": "sqlalchemy",
        "pandas": "pandas",
        "openpyxl": "openpyxl",
        "pyinstaller": "PyInstaller"  # Package name vs import name differ
    }
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        result = subprocess.run(
            [sys.executable, "-c", f"import {import_name}"],
            capture_output=True
        )
        if result.returncode == 0:
            print(f"      {Colors.GRAY}- {package_name}{Colors.RESET} {Colors.SUCCESS}[OK]{Colors.RESET}")
        else:
            missing_packages.append(package_name)
    
    if missing_packages:
        print_error(f"Missing packages: {', '.join(missing_packages)}")
        print(f"\n    {Colors.WARNING}Please install missing packages manually:{Colors.RESET}")
        print(f"    {Colors.INFO}py -m pip install {' '.join(missing_packages)}{Colors.RESET}\n")
        print(f"    {Colors.GRAY}Or if you're using a virtual environment:{Colors.RESET}")
        print(f"    {Colors.INFO}.\\venv\\Scripts\\python.exe -m pip install {' '.join(missing_packages)}{Colors.RESET}\n")
        return False
    
    print_success("All dependencies available")
    return True

def clean_previous_builds():
    """Step 2: Clean previous builds."""
    print_step("Step 2/9: Cleaning previous builds...")
    
    dirs_to_clean = ["build", "dist"]
    for dir_path in dirs_to_clean:
        if Path(dir_path).exists():
            shutil.rmtree(dir_path)
            print_success(f"Removed {dir_path}/")
    
    # Remove old spec backup files
    for backup in Path(".").glob("alnoor.spec.bak"):
        backup.unlink()
    
    print_success("Build directories cleaned")
    return True

def verify_database_isolation():
    """Step 3: Verify database isolation configuration."""
    print_step("Step 3/9: Verifying database isolation configuration...")
    
    # Check spec file
    spec_content = Path("alnoor.spec").read_text()
    if "'data'" in spec_content and "datas=" in spec_content:
        print_error("ERROR: data folder is included in alnoor.spec!")
        print_error("The development database would be packaged with the installer.")
        print_error("Please remove ('data', 'data') from the datas list in alnoor.spec")
        return False
    print_success("Spec file does not include data folder")
    
    # Check db_manager.py
    db_manager_content = Path("src/database/db_manager.py").read_text()
    if "getattr(sys, 'frozen', False)" in db_manager_content:
        print_success("Database manager has environment detection")
    else:
        print_warning("Warning: sys.frozen detection not found in db_manager.py")
        print_warning("The app may not create database in correct location")
    
    print_success("Database isolation verified")
    return True

def build_executable():
    """Step 4: Build executable with PyInstaller."""
    print_step("Step 4/9: Building executable with PyInstaller...")
    print(f"    {Colors.GRAY}This may take several minutes...{Colors.RESET}")
    
    build_start = datetime.now()
    
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "alnoor.spec"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print_error("PyInstaller build failed!")
        print(f"\n{Colors.ERROR}Error output:{Colors.RESET}")
        print(result.stderr)
        print(f"\n    {Colors.ERROR}Run manually for detailed error: {sys.executable} -m PyInstaller --clean alnoor.spec{Colors.RESET}")
        return False
    
    build_duration = (datetime.now() - build_start).total_seconds()
    print_success(f"Build completed in {build_duration:.1f} seconds")
    return True

def verify_build_output():
    """Step 5: Verify build output."""
    print_step("Step 5/9: Verifying build output...")
    
    exe_path = Path(f"dist/{EXECUTABLE_NAME}.exe")
    if not exe_path.exists():
        print_error(f"Executable not found at {exe_path}")
        return False
    print_success(f"Executable created: {exe_path}")
    
    # Get file size
    exe_size = exe_path.stat().st_size / (1024 * 1024)
    print_success(f"Executable size: {exe_size:.2f} MB")
    
    # Verify no database files in dist
    db_files = list(Path("dist").rglob("*.db"))
    if db_files:
        print_error("ERROR: Database files found in dist folder!")
        for db_file in db_files:
            print(f"      {Colors.ERROR}- {db_file}{Colors.RESET}")
        print_error("Development database was packaged. Build aborted.")
        return False
    print_success("No database files in distribution (verified)")
    
    # Verify no data directory
    if Path("dist/data").exists():
        print_error("ERROR: data directory found in dist folder!")
        print_error("Development data was packaged. Build aborted.")
        return False
    print_success("No data directory in distribution (verified)")
    
    print_success("Build verification passed")
    return True, exe_size

def create_release_directory(release_dir):
    """Step 6: Create release directory."""
    print_step("Step 6/9: Creating release directory...")
    
    release_path = Path(release_dir)
    if release_path.exists():
        print_warning("Release directory already exists, will overwrite contents")
    else:
        release_path.mkdir(parents=True, exist_ok=True)
        print_success(f"Created directory: {release_dir}")
    
    return True

def create_installer(version, release_dir, exe_size):
    """Step 7: Create Inno Setup installer."""
    print_step("Step 7/9: Creating installer...")
    
    inno_setup_path = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
    if not inno_setup_path.exists():
        print_warning("Inno Setup not found at default location")
        print_warning("Skipping installer creation. Only portable executable will be available.")
        
        # Copy executable to release folder (check both possible locations)
        exe_src = Path(f"dist/{EXECUTABLE_NAME}.exe")
        if not exe_src.exists():
            exe_src = Path(f"dist/{EXECUTABLE_NAME}/{EXECUTABLE_NAME}.exe")
        
        if exe_src.exists():
            shutil.copy2(exe_src, f"{release_dir}/{EXECUTABLE_NAME}.exe")
            print_success("Copied portable executable to release folder")
        else:
            print_error("Could not find executable to copy")
        return False
    
    # Create Inno Setup script
    iss_content = f"""
; Alnoor Medical Services Installer Script
; Generated automatically by build_installer.py
; Version: {version}

#define MyAppName "{APP_NAME}"
#define MyAppVersion "{version}"
#define MyAppPublisher "{APP_AUTHOR}"
#define MyAppURL "{APP_URL}"
#define MyAppExeName "{EXECUTABLE_NAME}.exe"
#define MyAppId "{{{{{APP_ID}}}}}"

[Setup]
; IMPORTANT: Keep AppId the same across versions for proper upgrades
AppId={{#MyAppId}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputDir={release_dir}
OutputBaseFilename=AlnoorMedicalServices-Setup-v{version}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayIcon={{app}}\\{{#MyAppExeName}}
VersionInfoVersion={version}.0
VersionInfoCompany={{#MyAppPublisher}}
VersionInfoDescription={{#MyAppName}} Installer
VersionInfoCopyright=Copyright (C) {datetime.now().year} {{#MyAppPublisher}}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "dist\\{{#MyAppExeName}}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "dist\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  OldVersion: String;
  IsUpgrade: Boolean;

function InitializeSetup(): Boolean;
begin
  IsUpgrade := RegQueryStringValue(HKLM, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{{#MyAppId}}_is1', 'DisplayVersion', OldVersion);
  
  if IsUpgrade then
  begin
    Log('Detected existing installation: ' + OldVersion);
    if MsgBox('Version ' + OldVersion + ' is currently installed.' + #13#10#13#10 +
              'This will upgrade to version {{#MyAppVersion}}.' + #13#10#13#10 +
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
    if IsUpgrade then
    begin
      AppDataDir := ExpandConstant('{{localappdata}}\\{{#MyAppName}}\\database');
      DatabasePath := AppDataDir + '\\alnoor.db';
      
      if FileExists(DatabasePath) then
      begin
        BackupPath := AppDataDir + '\\alnoor_backup_' + OldVersion + '_' + GetDateTimeString('yyyymmdd_hhnnss', '-', ':') + '.db';
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
    if IsUpgrade then
      Log('Upgrade completed. Database preserved')
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
    AppDataDir := ExpandConstant('{{localappdata}}\\{{#MyAppName}}');
    DatabasePath := AppDataDir + '\\database\\alnoor.db';
    
    if FileExists(DatabasePath) then
    begin
      Response := MsgBox('Do you want to keep your database and settings?' + #13#10#13#10 +
                        'Choose YES to keep your data for future reinstallation.' + #13#10 +
                        'Choose NO to completely remove all data.',
                        mbConfirmation, MB_YESNO);
      
      if Response = IDNO then
      begin
        Log('User chose to delete data');
        DelTree(AppDataDir, True, True, True);
      end
      else
        Log('User data preserved');
    end;
  end;
end;
"""
    
    iss_path = "installer_script.iss"
    Path(iss_path).write_text(iss_content)
    print_success("Created Inno Setup script")
    
    # Run Inno Setup
    print(f"    {Colors.GRAY}Compiling installer...{Colors.RESET}")
    result = subprocess.run([str(inno_setup_path), iss_path, "/Q"], capture_output=True, text=True)
    
    # Find executable (one-file or one-folder build)
    exe_src = Path(f"dist/{EXECUTABLE_NAME}.exe")
    if not exe_src.exists():
        exe_src = Path(f"dist/{EXECUTABLE_NAME}/{EXECUTABLE_NAME}.exe")
    
    if result.returncode != 0:
        print_warning("Inno Setup compilation failed")
        if result.stderr:
            print(f"    {Colors.ERROR}Error: {result.stderr[:200]}{Colors.RESET}")
        if result.stdout:
            print(f"    {Colors.GRAY}Output: {result.stdout[:200]}{Colors.RESET}")
        print_warning("Continuing with portable executable only")
        if exe_src.exists():
            shutil.copy2(exe_src, f"{release_dir}/{EXECUTABLE_NAME}.exe")
        installer_created = False
    else:
        print_success("Installer created successfully")
        # Copy portable executable
        if exe_src.exists():
            shutil.copy2(exe_src, f"{release_dir}/{EXECUTABLE_NAME}-Portable.exe")
            print_success("Copied portable executable")
        installer_created = True
    
    # Clean up ISS file
    Path(iss_path).unlink(missing_ok=True)
    return installer_created

def generate_documentation(version, release_dir):
    """Step 8: Generate documentation."""
    print_step("Step 8/9: Generating documentation...")
    
    python_version = subprocess.run([sys.executable, "--version"], capture_output=True, text=True).stdout.strip()
    
    # Create README
    readme = f"""# {APP_NAME} v{version}

## Installation

### Option 1: Installer (Recommended)
1. Run `AlnoorMedicalServices-Setup-v{version}.exe`
2. Follow the installation wizard
3. Launch from Start Menu or Desktop shortcut

### Option 2: Portable Executable
1. Extract `{EXECUTABLE_NAME}-Portable.exe` to any folder
2. Run `{EXECUTABLE_NAME}-Portable.exe`
3. No installation required

## Database Location

The application creates its database automatically on first run:

- **Installed Version**: `%LOCALAPPDATA%\\{APP_NAME}\\database\\alnoor.db`
- **Portable Version**: `%LOCALAPPDATA%\\{APP_NAME}\\database\\alnoor.db`

## Important Notes

⚠️ **Fresh Database**: This installation will create a NEW empty database.

✅ **Data Isolation**: Your production data is completely separate from development.

⚠️ **Backup Regularly**: Use File → Backup Database to create backups.

## Multi-User LAN Support

✅ SQLite WAL mode enabled for concurrent access
✅ Supports multiple users on network shares
✅ 30-second timeout with automatic retry
✅ Transaction-based operations prevent corruption

## System Requirements

- Windows 10 or later (64-bit)
- 4 GB RAM minimum
- 200 MB free disk space

## Support

GitHub: {APP_URL}

## Version Information

- Version: {version}
- Build Date: {datetime.now().strftime('%Y-%m-%d')}
- Python Version: {python_version}

---

© {datetime.now().year} {APP_AUTHOR}
"""
    
    Path(f"{release_dir}/README.txt").write_text(readme, encoding='utf-8')
    print_success("Created README.txt")
    
    # Copy network deployment guides
    network_guide = Path("NETWORK_DEPLOYMENT_GUIDE.md")
    quickstart = Path("NETWORK_DEPLOYMENT_QUICKSTART.md")
    config_example = Path("config.ini.example")
    
    if network_guide.exists():
        shutil.copy2(network_guide, f"{release_dir}/NETWORK_DEPLOYMENT_GUIDE.md")
        print_success("Copied NETWORK_DEPLOYMENT_GUIDE.md")
    
    if quickstart.exists():
        shutil.copy2(quickstart, f"{release_dir}/NETWORK_DEPLOYMENT_QUICKSTART.md")
        print_success("Copied NETWORK_DEPLOYMENT_QUICKSTART.md")
    
    simple_guide = Path("SIMPLE_INSTALLATION_GUIDE.md")
    if simple_guide.exists():
        shutil.copy2(simple_guide, f"{release_dir}/SIMPLE_INSTALLATION_GUIDE.md")
        print_success("Copied SIMPLE_INSTALLATION_GUIDE.md")
    
    if config_example.exists():
        shutil.copy2(config_example, f"{release_dir}/config.ini.example")
        print_success("Copied config.ini.example")
    
    # Create Release Notes
    release_notes = f"""===========================================
{APP_NAME} - Release Notes
Version {version}
===========================================

Build Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

FEATURES
--------

✨ Multi-User LAN Support
   - SQLite WAL mode for concurrent access
   - Multiple users can work simultaneously
   - Automatic conflict resolution

✨ Backup & Restore System
   - File → Backup Database
   - Automatic timestamped backups
   - One-click restore from backups

✨ Undo Verification
   - Tools → Undo Verification (Ctrl+Z)
   - Revert recent verification mistakes
   - Filter by timeframe

✨ Update-Safe Architecture
   - Database in AppData (never touched by updates)
   - Application in Program Files (updated safely)
   - Automatic migrations on first launch

INSTALLATION
------------

✅ Clean installation (no data migration needed)
✅ Database created automatically on first run
✅ Multi-user support (WAL mode)
✅ Update-safe database location

For questions or support:
GitHub: {APP_URL}

===========================================
© {datetime.now().year} {APP_AUTHOR}
===========================================
"""
    
    Path(f"{release_dir}/RELEASE_NOTES.txt").write_text(release_notes, encoding='utf-8')
    print_success("Created RELEASE_NOTES.txt")
    return True

def generate_checksums(release_dir):
    """Step 9: Generate checksums."""
    print_step("Step 9/9: Generating checksums...")
    
    version = release_dir.split('/')[-1].replace('v', '')
    checksum_content = f"""SHA256 Checksums for {APP_NAME} v{version}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
    
    release_files = [f for f in Path(release_dir).iterdir() if f.is_file() and f.name != "CHECKSUMS.txt"]
    for file_path in release_files:
        file_hash = calculate_sha256(file_path)
        checksum_content += f"{file_hash}  {file_path.name}\n"
        print(f"    {Colors.GRAY}{file_path.name}:{Colors.RESET} {Colors.SUCCESS}{file_hash[:16]}...{Colors.RESET}")
    
    Path(f"{release_dir}/CHECKSUMS.txt").write_text(checksum_content)
    print_success("Created CHECKSUMS.txt")
    return True

def print_summary(release_dir, exe_size):
    """Print build summary."""
    print(f"\n{Colors.BOLD}{Colors.SUCCESS}")
    print("============================================")
    print("  Build Completed Successfully!")
    print("============================================")
    print(f"{Colors.RESET}")
    
    print(f"Release Package: {Colors.INFO}{release_dir}{Colors.RESET}")
    
    print(f"\n{Colors.INFO}Package Contents:{Colors.RESET}")
    for file_path in Path(release_dir).iterdir():
        if file_path.is_file():
            size_kb = file_path.stat().st_size / 1024
            print(f"  {Colors.SUCCESS}-{Colors.RESET} {file_path.name} {Colors.GRAY}({size_kb:.2f} KB){Colors.RESET}")
    
    print(f"\n{Colors.INFO}Database Isolation:{Colors.RESET}")
    print(f"  {Colors.SUCCESS}[OK]{Colors.RESET} Development database NOT included")
    print(f"  {Colors.SUCCESS}[OK]{Colors.RESET} Fresh database will be created on first run")
    print(f"  {Colors.SUCCESS}[OK]{Colors.RESET} Location: {Colors.GRAY}%LOCALAPPDATA%\\{APP_NAME}\\database\\{Colors.RESET}")
    
    print(f"\n{Colors.INFO}Next Steps:{Colors.RESET}")
    print("  1. Test the installer on a clean machine")
    print("  2. Verify database is created in AppData")
    print("  3. Test all features with fresh database")
    print("  4. Distribute to users")
    
    print(f"\n{Colors.INFO}============================================{Colors.RESET}\n")

# ============================================
# Main Function
# ============================================

def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description='Build Alnoor Medical Services installer')
    parser.add_argument('--version', help='Version number (e.g., 1.0.2)')
    parser.add_argument('--prerelease', help='Prerelease identifier (e.g., beta.1)', default='')
    args = parser.parse_args()
    
    # Determine version
    version = args.version if args.version else auto_detect_version()
    full_version = f"{version}-{args.prerelease}" if args.prerelease else version
    release_dir = f"release/v{full_version}"
    
    print(f"\n{Colors.BOLD}{Colors.INFO}")
    print("============================================")
    print(f"  {APP_NAME}")
    print(f"  Release Builder v{version}")
    print("============================================")
    print(f"{Colors.RESET}\n")
    
    # Execute build steps
    if not validate_environment():
        sys.exit(1)
    
    if not clean_previous_builds():
        sys.exit(1)
    
    if not verify_database_isolation():
        sys.exit(1)
    
    if not build_executable():
        sys.exit(1)
    
    success, exe_size = verify_build_output()
    if not success:
        sys.exit(1)
    
    if not create_release_directory(release_dir):
        sys.exit(1)
    
    installer_created = create_installer(version, release_dir, exe_size)
    
    if not generate_documentation(version, release_dir):
        sys.exit(1)
    
    if not generate_checksums(release_dir):
        sys.exit(1)
    
    print_summary(release_dir, exe_size)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

