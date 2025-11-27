; Alnoor Medical Services - Inno Setup Installer Script
; ======================================================
;
; This script creates a Windows installer for the
; Alnoor Medical Services application.
;
; Prerequisites:
;   - Inno Setup 6 installed (https://jrsoftware.org/isdl.php)
;   - Executable built: dist/AlnoorMedicalServices.exe
;
; Usage:
;   ISCC.exe installer.iss
;
; Output:
;   installer/AlnoorMedicalServices_Setup_v1.0.0.exe

#define MyAppName "Alnoor Medical Services"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Alnoor Medical Services"
#define MyAppURL "https://www.alnoor-medical.example"
#define MyAppExeName "AlnoorMedicalServices.exe"

[Setup]
; NOTE: Generate a new GUID using Tools > Generate GUID in Inno Setup
AppId={{A8F3C2E1-5D4B-4A9C-8E7F-1B2C3D4E5F6A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; Output
OutputDir=installer
OutputBaseFilename=AlnoorMedicalServices_Setup_v{#MyAppVersion}

; Compression
Compression=lzma2/max
SolidCompression=yes

; Wizard appearance
WizardStyle=modern
; Note: Using default wizard images (removed custom image references)

; Icons (uncomment if icon file exists)
;SetupIconFile=resources\icon.ico
;UninstallDisplayIcon={app}\{#MyAppExeName}

; Version info
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoCopyright=Copyright (C) 2025 {#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Launch application at Windows startup"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "README.txt"
Source: "DEPLOYMENT.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "DEPLOYMENT_GUIDE.txt"

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
; Start Menu icons
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop icon (if task selected)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch icon (if task selected)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Dirs]
; Create application data directories
Name: "{localappdata}\{#MyAppName}"; Permissions: users-full
Name: "{localappdata}\{#MyAppName}\database"; Permissions: users-full
Name: "{localappdata}\{#MyAppName}\logs"; Permissions: users-full
Name: "{localappdata}\{#MyAppName}\exports"; Permissions: users-full
Name: "{localappdata}\{#MyAppName}\backups"; Permissions: users-full
Name: "{commondocs}\{#MyAppName}"; Permissions: users-full
Name: "{commondocs}\{#MyAppName}\Reports"; Permissions: users-full

[Run]
; Launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Custom installation logic

var
  DataDirPage: TInputDirWizardPage;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Check for required dependencies (if any)
  // Example: Check if Visual C++ Redistributable is installed
end;

procedure InitializeWizard;
begin
  // Create custom page for data directory selection (optional)
  DataDirPage := CreateInputDirPage(wpSelectDir,
    'Select Data Directory', 'Where should application data be stored?',
    'The application will store its database, logs, and exports in this location.' + #13#10#13#10 +
    'By default, it uses the Windows standard application data folder.',
    False, '');
  DataDirPage.Add('');
  DataDirPage.Values[0] := ExpandConstant('{localappdata}\{#MyAppName}');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  DataDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Get the data directory (use custom or default)
    DataDir := DataDirPage.Values[0];
    
    // Create subdirectories if they don't exist
    ForceDirectories(DataDir + '\database');
    ForceDirectories(DataDir + '\logs');
    ForceDirectories(DataDir + '\exports');
    ForceDirectories(DataDir + '\backups');
    
    // Create a configuration file with the data directory path
    SaveStringToFile(ExpandConstant('{app}\data_path.txt'), DataDir, False);
    
    // Log installation
    Log('Installation completed successfully');
    Log('Data directory: ' + DataDir);
  end;
end;

function GetDataDir(Param: String): String;
begin
  // Return the data directory for use in other sections
  Result := DataDirPage.Values[0];
end;

[UninstallDelete]
; Clean up application data on uninstall (optional - removes user data!)
; Uncomment with caution - this will delete user databases!
;Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"

[Messages]
; Custom messages
WelcomeLabel2=This will install [name/ver] on your computer.%n%nThis application helps track medical supplies and patient coupons.%n%nIt is recommended that you close all other applications before continuing.
FinishedHeadingLabel=Completing the [name] Setup Wizard
FinishedLabelNoIcons=Setup has finished installing [name] on your computer.
FinishedLabel=Setup has finished installing [name] on your computer. The application may be launched by selecting the installed shortcuts.

[Registry]
; Add to Windows startup (if task selected)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletevalue; Tasks: startupicon

; Save installation path for application
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "DataPath"; ValueData: "{code:GetDataDir}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
