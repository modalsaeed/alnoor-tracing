# Alnoor Medical Services v1.0.9

## 📦 Package Contents

This release includes TWO deployment options:

### Option 1: Single PC / RDP Deployment
- Use the main installer for standalone or RDP-based multi-user setup

### Option 2: API Server Multi-User Deployment  
- Server files in `Server/` folder (for IT person)
- Client installer (same as Option 1, just needs config.ini)

See DEPLOYMENT_OPTIONS.md for detailed comparison.

---

## 🖥️ SINGLE PC INSTALLATION

### Option 1: Installer (Recommended)
1. Run `AlnoorMedicalServices-Setup-v1.0.9.exe`
2. Follow the installation wizard
3. Launch from Start Menu or Desktop shortcut

### Option 2: Portable Executable
1. Extract `AlnoorMedicalServices-Portable.exe` to any folder
2. Run `AlnoorMedicalServices-Portable.exe`
3. No installation required

**Database Location**: `%LOCALAPPDATA%\Alnoor Medical Services\database\alnoor.db`

---

## 👥 MULTI-USER INSTALLATION

### Choose Your Deployment Method:

**METHOD A: Remote Desktop (Simpler)**
- Setup time: 30 minutes
- Users: 2-4 concurrent
- Users work via Remote Desktop
- See: Setup-MultiUser.ps1 script

**METHOD B: API Server (Better UX)**  
- Setup time: 30 minutes
- Users: 4-10+ concurrent
- Each user works on their own PC
- See: Server/ folder + API_SERVER_SETUP_GUIDE.md

---

## 📁 Folder Structure

```
release/v1.0.9/
├── AlnoorMedicalServices-Setup-v1.0.9.exe    ← Install on all PCs
├── AlnoorMedicalServices-Portable.exe            ← Optional portable version
│
├── Server/                                        ← FOR API SERVER SETUP ONLY
│   ├── API_SERVER_SETUP_GUIDE.md                 ← Give to IT person
│   ├── start_server.bat                          ← Server startup script
│   ├── start_server.py                           ← Cross-platform launcher
│   ├── test_api_server.py                        ← Test script
│   └── src/
│       ├── api_server.py                         ← Main API server
│       └── database/
│           └── db_client.py                      ← HTTP client
│
├── Documentation/                                 ← SETUP GUIDES
│   ├── API_SERVER_QUICKSTART.md                  ← Quick decision guide
│   ├── DEPLOYMENT_OPTIONS.md                     ← Compare all options
│   ├── SOLUTION_CONCURRENT_USERS.md              ← Multi-user solutions
│   ├── SIMPLE_INSTALLATION_GUIDE.md              ← Non-technical guide
│   └── config.ini.example                        ← Configuration examples
│
├── README.txt                                     ← START HERE
├── RELEASE_NOTES.txt                             ← What's new
└── CHECKSUMS.txt                                  ← File verification
```

---

## 🚀 Quick Start Guide

### For Single User:
1. Run installer
2. Launch app
3. Start working!

### For Multi-User (Remote Desktop):
1. Install on server PC
2. Run `Setup-MultiUser.ps1` (choose Option 2 or 3)  
3. Users Remote Desktop to server

### For Multi-User (API Server):
1. Give `Server/` folder to IT person
2. IT person follows API_SERVER_SETUP_GUIDE.md
3. On each client PC:
   - Install app
   - Create config.ini with server URL
4. Users work on their own PCs!

---

## ⚠️ Important Notes

✅ **Fresh Database**: Creates NEW empty database on first run

✅ **Data Isolation**: Your data is separate from development

✅ **Backward Compatible**: All existing deployments still work

⚠️ **Network Shares**: Do NOT use network shares for database with concurrent users (causes data corruption). Use RDP or API server instead.

---

## 🔧 Configuration Files

### Single PC (Default)
No config.ini needed - works out of the box!

### Multi-User RDP
Create `C:\Program Files\Alnoor Medical Services\config.ini`:
```ini
[database]
path = C:\ProgramData\AlnoorDB\alnoor.db
```

### Multi-User API Server
Create `C:\Program Files\Alnoor Medical Services\config.ini`:
```ini
[server]
mode = client
server_url = http://192.168.1.10:5000
```

See `Documentation/config.ini.example` for all options.

---

## 📊 System Requirements

- Windows 10 or later (64-bit)
- 4 GB RAM minimum
- 200 MB free disk space
- **Server PC (API mode)**: Python 3.8+ required

---

## 📞 Support

GitHub: https://github.com/modalsaeed/alnoor-tracing

For setup help:
- Single PC: See SIMPLE_INSTALLATION_GUIDE.md
- Multi-User: See API_SERVER_SETUP_GUIDE.md
- All Options: See DEPLOYMENT_OPTIONS.md

---

## Version Information

- Version: 1.0.9
- Build Date: 2025-12-25
- Python Version: Python 3.14.2

---

© 2025 Alnoor Medical Services
