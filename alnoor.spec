# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Alnoor Medical Services Tracking App.

This spec file configures PyInstaller to build a standalone Windows executable
for the Alnoor Medical Services database tracking application.

Usage:
    pyinstaller alnoor.spec

The resulting executable will be in the 'dist' folder.
"""

import sys
from pathlib import Path

# Define paths
project_root = Path.cwd()
src_dir = project_root / 'src'

block_cipher = None

# Analysis: Collect all Python modules and dependencies
a = Analysis(
    ['src/main.py'],  # Entry point script
    pathex=[str(project_root), str(src_dir)],
    binaries=[],
    datas=[
        # Include template files for delivery notes
        ('resources/templates/*.xlsx', 'resources/templates'),
        # Include config.ini.example for network deployment
        ('config.ini.example', '.'),
        # DO NOT include data directory - each installation creates its own database
        # Database will be created in user's AppData directory on first run
    ],
    hiddenimports=[
        # PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        
        # SQLAlchemy and database
        'sqlalchemy',
        'sqlalchemy.orm',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.sql',
        'sqlalchemy.dialects.sqlite',
        
        # Application modules
        'src.database',
        'src.database.db_manager',
        'src.database.models',
        'src.services',
        'src.services.stock_service',
        'src.ui',
        'src.ui.main_window',
        'src.ui.widgets',
        'src.ui.widgets.dashboard_widget',
        'src.ui.widgets.products_widget',
        'src.ui.widgets.purchase_orders_widget',
        'src.ui.widgets.coupons_widget',
        'src.ui.widgets.transactions_widget',
        'src.ui.widgets.medical_centres_widget',
        'src.ui.widgets.distribution_locations_widget',
        'src.ui.widgets.reports_widget',
        'src.ui.dialogs',
        'src.ui.dialogs.transaction_dialog',
        'src.ui.dialogs.verify_coupon_dialog',
        'src.utils',
        'src.utils.validators',
        'src.utils.style_constants',
        
        # Data processing
        'pandas',
        'openpyxl',
        'dateutil',
        'pytz',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules
        'pytest',
        'pytest-qt',
        'pytest-cov',
        '_pytest',
        'tests',
        
        # Exclude development tools
        'black',
        'flake8',
        'pylint',
        
        # Exclude unused modules to reduce size
        'matplotlib',
        'numpy.tests',
        'pandas.tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ: Create Python archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# EXE: Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AlnoorMedicalServices',  # Executable name
    debug=False,  # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX (if available)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if (project_root / 'resources' / 'icon.ico').exists() else None,  # Application icon
    version_file=None,  # Can add version info later
)

# COLLECT: Create folder with all dependencies (alternative to one-file)
# Uncomment below if you prefer one-folder distribution instead of one-file
"""
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
"""
