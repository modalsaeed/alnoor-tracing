==============================================
Alnoor Medical Services - Tracking Application
Version 1.0.0
==============================================

Thank you for using Alnoor Medical Services Tracking Application!

ABOUT
-----
This application helps manage and track:
  • Product catalog
  • Purchase orders from Ministry of Health
  • Patient coupons with CPR validation
  • Verification workflow (FIFO stock deduction)
  • Medical centres and distribution locations
  • Reports and activity logs

QUICK START
-----------
1. Double-click AlnoorMedicalServices.exe
2. The application will automatically create a database
3. Start by adding products (Products tab)
4. Add purchase orders (Purchase Orders tab)
5. Manage coupons (Coupons tab)
6. Generate reports (Reports tab)

SYSTEM REQUIREMENTS
-------------------
  • Operating System: Windows 10/11 (64-bit)
  • RAM: 4GB minimum (8GB recommended)
  • Disk Space: 100MB free space
  • Screen Resolution: 1280x720 or higher
  • Internet: Not required (runs completely offline)

FIRST RUN
---------
On first launch, the application will:
  • Create database directory
  • Initialize database schema
  • Set up activity logging

Database location:
  C:\Users\<YourName>\AppData\Local\Alnoor Medical Services\data\alnoor.db

Backups location:
  C:\Users\<YourName>\AppData\Local\Alnoor Medical Services\backups\

FEATURES
--------
✓ Product Management
  - Add, edit, delete products
  - Unique product references (auto-uppercase)
  - Search and filter

✓ Purchase Order Tracking
  - Track stock from Ministry of Health
  - FIFO (First-In-First-Out) stock deduction
  - Real-time stock levels
  - Color-coded stock indicators

✓ Coupon Verification
  - Patient CPR validation (Bahraini format)
  - Verification workflow with references
  - Automatic stock deduction
  - Verification history tracking

✓ Medical Centres & Locations
  - Manage medical centres
  - Track distribution locations
  - Contact information management

✓ Reports & Analytics
  - Stock summary reports
  - Coupon verification reports
  - Activity logs
  - CSV export functionality

✓ Backup & Restore
  - One-click database backup
  - Restore from backup files
  - Automatic timestamped backups

USAGE TIPS
----------
• Product References: Automatically converted to UPPERCASE
• CPR Format: Accepts XXXXXXXXX or XXX-XXX-XXX format
• Search: Use search boxes to quickly find records
• Stock Levels: Color-coded (Red: Low, Yellow: Medium, Green: Good)
• Verification: Requires available stock and valid CPR
• Backups: Recommended before major data changes

KEYBOARD SHORTCUTS
------------------
  Ctrl+N  - Add new record (in active tab)
  Ctrl+F  - Focus search box
  Ctrl+S  - Save (in dialogs)
  Esc     - Cancel (in dialogs)
  F5      - Refresh current view

COMMON TASKS
------------
Add a Product:
  1. Go to Products tab
  2. Click "Add Product"
  3. Fill in details (reference, name, description)
  4. Click "Save"

Create Purchase Order:
  1. Go to Purchase Orders tab
  2. Click "Add Purchase Order"
  3. Select product, enter PO reference and quantity
  4. Click "Save"

Verify Coupon:
  1. Go to Coupons tab
  2. Click "Verify Coupon"
  3. Enter coupon reference or search
  4. Enter verification reference
  5. Click "Verify"
  6. Stock automatically deducted (FIFO)

Generate Report:
  1. Go to Reports tab
  2. Select report type (Stock, Coupon, Activity)
  3. Set date range and filters
  4. Click "Generate Report"
  5. Export to CSV if needed

Backup Database:
  1. Click File → Backup Database
  2. Backup saved automatically with timestamp
  3. Location shown in success message

DATA SAFETY
-----------
• Automatic validation prevents invalid data
• Unique constraints prevent duplicates
• FIFO ensures correct stock deduction
• Activity logs track all changes
• Regular backups recommended

TROUBLESHOOTING
---------------
Application won't start:
  • Run as Administrator
  • Check Windows Event Viewer for errors
  • Ensure adequate disk space

Database errors:
  • Close and restart application
  • Restore from backup if needed
  • Check file permissions

Slow performance:
  • Close other applications
  • Check available RAM
  • Clear old activity logs

Can't verify coupon:
  • Ensure adequate stock available
  • Check CPR format (9 digits)
  • Verify coupon not already verified

DATA LOCATIONS
--------------
Application data is stored in:
  C:\Users\<YourName>\AppData\Local\Alnoor Medical Services\

Folders:
  data\       - Database files
  backups\    - Backup files
  logs\       - Activity logs (if enabled)

UNINSTALLATION
--------------
If installed via installer:
  1. Control Panel → Programs and Features
  2. Select "Alnoor Medical Services"
  3. Click "Uninstall"

If using standalone .exe:
  1. Delete AlnoorMedicalServices.exe
  2. Optionally delete data folder:
     C:\Users\<YourName>\AppData\Local\Alnoor Medical Services\

PRIVACY & SECURITY
------------------
• All data stored locally (no cloud/internet)
• Patient CPR data validated and sanitized
• No external connections required
• User responsible for data backup and security
• Consider encrypting sensitive backups

SUPPORT
-------
For questions, issues, or feature requests:
  Email: support@alnoor-medical.example
  Website: https://www.alnoor-medical.example

CREDITS
-------
Developed by: Alnoor Medical Services Development Team
Framework: PyQt6, SQLAlchemy
Testing: pytest
Packaging: PyInstaller

VERSION HISTORY
---------------
Version 1.0.0 (November 2025)
  • Initial release
  • Complete CRUD functionality
  • Verification workflow with FIFO
  • Reporting system
  • Backup/restore functionality

==============================================
Thank you for using Alnoor Medical Services!
==============================================

Last Updated: November 8, 2025
