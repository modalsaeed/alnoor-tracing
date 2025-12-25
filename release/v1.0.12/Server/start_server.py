#!/usr/bin/env python3
"""
Alnoor Medical Services - API Server Launcher
Cross-platform startup script for the API server
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Ensure Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")


def install_dependencies():
    """Install required packages"""
    required_packages = [
        'flask',
        'flask-cors',
        'sqlalchemy',
    ]
    
    print("\n📦 Checking dependencies...")
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"⚙️  Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed")


def get_local_ip():
    """Get local IP address"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unable to determine"


def main():
    """Main startup function"""
    print("=" * 60)
    print("Alnoor Medical Services - API Server Launcher")
    print("=" * 60)
    print()
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Get IP address
    local_ip = get_local_ip()
    
    print()
    print("=" * 60)
    print("🚀 Starting API Server...")
    print("=" * 60)
    print()
    print(f"Server will be accessible at:")
    print(f"  - Local: http://localhost:5000")
    print(f"  - Network: http://{local_ip}:5000")
    print()
    print("Other computers should connect to:")
    print(f"  http://{local_ip}:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # Start the server
    server_path = Path(__file__).parent / 'src' / 'api_server.py'
    subprocess.run([sys.executable, str(server_path)])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
