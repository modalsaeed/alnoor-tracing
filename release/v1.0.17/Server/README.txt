# Alnoor Medical Services - API Server Package

## 🎯 For IT Personnel Only

This folder contains the API server for multi-user deployment.

**DO NOT distribute this to end users!**  
End users only need the main installer + config.ini

---

## 📋 What You Need

1. Main server PC (Windows 10/11 or Windows Server)
2. Python 3.8+ installed
3. Network connectivity
4. 20 minutes of setup time

---

## 🚀 Quick Setup

### Step 1: Install Python (if not already installed)
1. Download: https://www.python.org/downloads/
2. Install with **"Add Python to PATH"** checked ✓
3. Verify: Open cmd, type `python --version`

### Step 2: Copy This Folder to Server PC
Copy entire `Server/` folder to: `C:\AlnoorServer\`

### Step 3: Start the Server
1. Navigate to `C:\AlnoorServer\`
2. Double-click `start_server.bat`
3. Note the IP address shown (e.g., 192.168.1.10)
4. Keep the window open!

### Step 4: Configure Firewall
Run in PowerShell (as Administrator):
```powershell
New-NetFirewallRule -DisplayName "Alnoor API Server" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Step 5: Test Server
Open browser: http://localhost:5000/health  
Should see: {"status": "healthy"}

---

## 👥 Client PC Configuration

On each user's PC:

1. Install main app: `AlnoorMedicalServices-Setup-v1.0.17.exe`

2. Create config.ini at:
   `C:\Program Files\Alnoor Medical Services\config.ini`

3. Content:
   ```ini
   [server]
   mode = client
   server_url = http://192.168.1.10:5000
   ```
   (Replace 192.168.1.10 with your server's IP)

4. Launch app - Done!

---

## 📚 Full Documentation

See: **API_SERVER_SETUP_GUIDE.md** (in this folder)

Complete step-by-step instructions with troubleshooting.

---

## 🧪 Testing

Run test script:
```cmd
cd C:\AlnoorServer
python test_api_server.py http://192.168.1.10:5000
```

Should show: ✅ All tests passed!

---

## 🆘 Common Issues

**"Python not recognized"**
- Reinstall Python with "Add to PATH" checked

**"Cannot connect from client"**
- Check firewall rule (Step 4)
- Verify server is running
- Ping server: `ping 192.168.1.10`

**"Port 5000 already in use"**
- Another app is using port 5000
- See troubleshooting in API_SERVER_SETUP_GUIDE.md

---

## 📞 Need Help?

Full guide: API_SERVER_SETUP_GUIDE.md  
Support: https://github.com/modalsaeed/alnoor-tracing

---

**Remember**: Keep server running during work hours!
Press Ctrl+C in server window to stop.
