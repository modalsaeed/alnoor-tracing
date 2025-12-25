# Alnoor Multi-User Setup Script
# This script helps you set up the application for Remote Desktop multi-user access

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Alnoor Medical Services" -ForegroundColor Cyan
Write-Host "Multi-User Setup Wizard" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Present options
Write-Host "Choose your setup type:`n" -ForegroundColor Yellow
Write-Host "  [1] Single PC Setup (Default)" -ForegroundColor White
Write-Host "      - Database in user's AppData folder" -ForegroundColor Gray
Write-Host "      - One user per PC" -ForegroundColor Gray
Write-Host "      - No configuration needed`n" -ForegroundColor Gray

Write-Host "  [2] Multi-User Setup - This PC as Server" -ForegroundColor White
Write-Host "      - Database on this PC (C:\ProgramData\AlnoorDB\)" -ForegroundColor Gray
Write-Host "      - Other users connect via Remote Desktop" -ForegroundColor Gray
Write-Host "      - Perfect if you don't have server access`n" -ForegroundColor Gray

Write-Host "  [3] Multi-User Setup - Server PC" -ForegroundColor White
Write-Host "      - For installing on dedicated server" -ForegroundColor Gray
Write-Host "      - Users connect to server via Remote Desktop" -ForegroundColor Gray
Write-Host "      - Best for production use`n" -ForegroundColor Gray

$choice = Read-Host "Enter your choice (1, 2, or 3)"

switch ($choice) {
    "1" {
        Write-Host "`n✓ Single PC Setup Selected" -ForegroundColor Green
        Write-Host "`nNo configuration needed!" -ForegroundColor Green
        Write-Host "The application will use default settings." -ForegroundColor White
        Write-Host "Database location: %LOCALAPPDATA%\Alnoor Medical Services\database\" -ForegroundColor Gray
        
        # Remove config.ini if exists
        $configPath = "C:\Program Files\Alnoor Medical Services\config.ini"
        if (Test-Path $configPath) {
            Write-Host "`nRemoving existing config.ini..." -ForegroundColor Yellow
            Remove-Item $configPath -Force
            Write-Host "✓ Config removed - using default settings" -ForegroundColor Green
        }
        
        Write-Host "`n✓ Setup complete!" -ForegroundColor Green
        Write-Host "You can now run Alnoor Medical Services normally." -ForegroundColor White
    }
    
    "2" {
        Write-Host "`n✓ Multi-User Setup - This PC as Server" -ForegroundColor Green
        Write-Host "`nSetting up this PC for Remote Desktop access..." -ForegroundColor White
        
        # Step 1: Create database directory
        Write-Host "`n[1/5] Creating database directory..." -ForegroundColor Yellow
        $dbPath = "C:\ProgramData\AlnoorDB"
        New-Item -Path $dbPath -ItemType Directory -Force | Out-Null
        Write-Host "  ✓ Created: $dbPath" -ForegroundColor Green
        
        # Step 2: Set permissions
        Write-Host "`n[2/5] Setting permissions..." -ForegroundColor Yellow
        icacls $dbPath /grant Users:"(OI)(CI)F" /T | Out-Null
        Write-Host "  ✓ All users can read/write database" -ForegroundColor Green
        
        # Step 3: Create config.ini
        Write-Host "`n[3/5] Creating configuration file..." -ForegroundColor Yellow
        $configContent = @"
[database]
path = C:\ProgramData\AlnoorDB\alnoor.db

# Multi-User RDP Setup
# This PC acts as the database server
# Other users connect here via Remote Desktop
"@
        $configPath = "C:\Program Files\Alnoor Medical Services\config.ini"
        $configContent | Set-Content -Path $configPath -Force
        Write-Host "  ✓ Config created: $configPath" -ForegroundColor Green
        
        # Step 4: Enable Remote Desktop
        Write-Host "`n[4/5] Enabling Remote Desktop..." -ForegroundColor Yellow
        try {
            Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -Value 0 -ErrorAction Stop
            Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction Stop
            Write-Host "  ✓ Remote Desktop enabled" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ Could not enable Remote Desktop automatically" -ForegroundColor Yellow
            Write-Host "  Please enable it manually: Settings → Remote Desktop → ON" -ForegroundColor Yellow
        }
        
        # Step 5: Display connection info
        Write-Host "`n[5/5] Getting connection information..." -ForegroundColor Yellow
        $computerName = $env:COMPUTERNAME
        $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.PrefixOrigin -eq "Dhcp" -or $_.PrefixOrigin -eq "Manual"} | Select-Object -First 1).IPAddress
        $username = $env:USERNAME
        
        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host "Setup Complete!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        
        Write-Host "`nThis PC is now the database server." -ForegroundColor White
        Write-Host "`nConnection Information:" -ForegroundColor Yellow
        Write-Host "  Computer Name: $computerName" -ForegroundColor White
        Write-Host "  IP Address: $ipAddress" -ForegroundColor White
        Write-Host "  Username: $username" -ForegroundColor White
        Write-Host "  Database: C:\ProgramData\AlnoorDB\alnoor.db" -ForegroundColor White
        
        Write-Host "`nFor other users to connect:" -ForegroundColor Yellow
        Write-Host "  1. Open 'Remote Desktop Connection' on their PC" -ForegroundColor White
        Write-Host "  2. Computer: $computerName (or $ipAddress)" -ForegroundColor White
        Write-Host "  3. Username: $username" -ForegroundColor White
        Write-Host "  4. Password: [Your Windows password]" -ForegroundColor White
        Write-Host "  5. After connecting, run Alnoor Medical Services" -ForegroundColor White
        
        Write-Host "`n⚠ IMPORTANT:" -ForegroundColor Yellow
        Write-Host "  - Keep this PC on during work hours" -ForegroundColor White
        Write-Host "  - Don't let it sleep" -ForegroundColor White
        Write-Host "  - First launch will create the database" -ForegroundColor White
        
        # Save connection info to file
        $infoFile = "$env:USERPROFILE\Desktop\Alnoor_Connection_Info.txt"
        @"
Alnoor Medical Services - Connection Information
================================================

This PC is the database server.

Connection Details:
  Computer Name: $computerName
  IP Address: $ipAddress
  Username: $username
  Password: [Your Windows password]

For Other Users:
  1. Open 'Remote Desktop Connection'
  2. Enter Computer Name or IP Address
  3. Enter Username and Password
  4. Click Connect
  5. Run Alnoor Medical Services

Database Location: C:\ProgramData\AlnoorDB\alnoor.db

Setup Date: $(Get-Date -Format "yyyy-MM-dd HH:mm")
"@ | Set-Content -Path $infoFile
        
        Write-Host "`n✓ Connection info saved to Desktop" -ForegroundColor Green
    }
    
    "3" {
        Write-Host "`n✓ Multi-User Setup - Server PC" -ForegroundColor Green
        Write-Host "`nSetting up for dedicated server..." -ForegroundColor White
        
        # Step 1: Create database directory
        Write-Host "`n[1/5] Creating database directory..." -ForegroundColor Yellow
        $dbPath = "C:\ProgramData\AlnoorDB"
        New-Item -Path $dbPath -ItemType Directory -Force | Out-Null
        Write-Host "  ✓ Created: $dbPath" -ForegroundColor Green
        
        # Step 2: Set permissions
        Write-Host "`n[2/5] Setting permissions..." -ForegroundColor Yellow
        icacls $dbPath /grant Users:"(OI)(CI)F" /T | Out-Null
        Write-Host "  ✓ All users can read/write database" -ForegroundColor Green
        
        # Step 3: Create config.ini
        Write-Host "`n[3/5] Creating configuration file..." -ForegroundColor Yellow
        $configContent = @"
[database]
path = C:\ProgramData\AlnoorDB\alnoor.db

# Multi-User Server Setup
# This is the dedicated server
# Users connect here via Remote Desktop
"@
        $configPath = "C:\Program Files\Alnoor Medical Services\config.ini"
        $configContent | Set-Content -Path $configPath -Force
        Write-Host "  ✓ Config created: $configPath" -ForegroundColor Green
        
        # Step 4: Enable Remote Desktop
        Write-Host "`n[4/5] Enabling Remote Desktop..." -ForegroundColor Yellow
        try {
            Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -Value 0 -ErrorAction Stop
            Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction Stop
            Write-Host "  ✓ Remote Desktop enabled" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ Could not enable Remote Desktop automatically" -ForegroundColor Yellow
            Write-Host "  Please enable it manually: Settings → Remote Desktop → ON" -ForegroundColor Yellow
        }
        
        # Step 5: Create backup script
        Write-Host "`n[5/5] Creating backup script..." -ForegroundColor Yellow
        $backupScript = @"
# Alnoor Database Backup Script
`$DatabasePath = "C:\ProgramData\AlnoorDB\alnoor.db"
`$BackupFolder = "C:\ProgramData\AlnoorDB\Backups"
`$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
`$BackupPath = "`$BackupFolder\alnoor_backup_`$Timestamp.db"

# Create backup folder if it doesn't exist
if (!(Test-Path `$BackupFolder)) {
    New-Item -ItemType Directory -Path `$BackupFolder | Out-Null
}

# Copy database to backup
if (Test-Path `$DatabasePath) {
    Copy-Item `$DatabasePath `$BackupPath -Force
    Write-Host "Backup completed: `$BackupPath" -ForegroundColor Green
    
    # Keep only last 30 days of backups
    Get-ChildItem `$BackupFolder -Filter "alnoor_backup_*.db" | 
        Where-Object { `$_.LastWriteTime -lt (Get-Date).AddDays(-30) } | 
        Remove-Item -Force
    Write-Host "Old backups cleaned up (kept last 30 days)" -ForegroundColor Gray
} else {
    Write-Host "ERROR: Database not found at `$DatabasePath" -ForegroundColor Red
}
"@
        $backupScriptPath = "C:\ProgramData\AlnoorDB\Backup-Database.ps1"
        $backupScript | Set-Content -Path $backupScriptPath -Force
        Write-Host "  ✓ Backup script created: $backupScriptPath" -ForegroundColor Green
        
        # Display connection info
        $computerName = $env:COMPUTERNAME
        $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.PrefixOrigin -eq "Dhcp" -or $_.PrefixOrigin -eq "Manual"} | Select-Object -First 1).IPAddress
        
        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host "Server Setup Complete!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        
        Write-Host "`nServer Information:" -ForegroundColor Yellow
        Write-Host "  Computer Name: $computerName" -ForegroundColor White
        Write-Host "  IP Address: $ipAddress" -ForegroundColor White
        Write-Host "  Database: C:\ProgramData\AlnoorDB\alnoor.db" -ForegroundColor White
        Write-Host "  Backup Script: C:\ProgramData\AlnoorDB\Backup-Database.ps1" -ForegroundColor White
        
        Write-Host "`nNext Steps:" -ForegroundColor Yellow
        Write-Host "  1. Launch Alnoor Medical Services to create database" -ForegroundColor White
        Write-Host "  2. Set up automated backups (Task Scheduler)" -ForegroundColor White
        Write-Host "  3. Give connection info to users" -ForegroundColor White
        
        Write-Host "`n⚠ Don't forget to schedule automated backups!" -ForegroundColor Yellow
        Write-Host "  Run: schtasks /create /tn ""Alnoor Backup"" /tr ""powershell -File C:\ProgramData\AlnoorDB\Backup-Database.ps1"" /sc daily /st 02:00" -ForegroundColor Gray
    }
    
    default {
        Write-Host "`nERROR: Invalid choice. Please run the script again." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
