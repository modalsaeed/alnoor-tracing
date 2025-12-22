# Alnoor Medical Services v1.0.3

## Installation

### Option 1: Installer (Recommended)
1. Run `AlnoorMedicalServices-Setup-v1.0.3.exe`
2. Follow the installation wizard
3. Launch from Start Menu or Desktop shortcut

### Option 2: Portable Executable
1. Extract `AlnoorMedicalServices-Portable.exe` to any folder
2. Run `AlnoorMedicalServices-Portable.exe`
3. No installation required

## Database Location

The application creates its database automatically on first run:

- **Installed Version**: `%LOCALAPPDATA%\Alnoor Medical Services\database\alnoor.db`
- **Portable Version**: `%LOCALAPPDATA%\Alnoor Medical Services\database\alnoor.db`

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

GitHub: https://github.com/modalsaeed/alnoor-tracing

## Version Information

- Version: 1.0.3
- Build Date: 2025-12-22
- Python Version: Python 3.13.1

---

© 2025 Alnoor Medical Services
