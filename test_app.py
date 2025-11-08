"""Quick test script to verify all imports work."""

import sys
print("Python version:", sys.version)
print("=" * 50)

try:
    print("Testing imports...")
    
    print("  ✓ PyQt6...", end="")
    from PyQt6.QtWidgets import QApplication
    print(" OK")
    
    print("  ✓ SQLAlchemy...", end="")
    from sqlalchemy import create_engine
    print(" OK")
    
    print("  ✓ pandas...", end="")
    import pandas
    print(" OK")
    
    print("  ✓ Database models...", end="")
    from src.database.models import Product, PurchaseOrder, PatientCoupon
    print(" OK")
    
    print("  ✓ Database manager...", end="")
    from src.database.db_manager import DatabaseManager
    print(" OK")
    
    print("  ✓ Style constants...", end="")
    from src.utils.style_constants import Colors, IconStyles, Fonts
    print(" OK")
    
    print("  ✓ Main window...", end="")
    from src.ui.main_window import MainWindow
    print(" OK")
    
    print("=" * 50)
    print("✅ All imports successful!")
    print("=" * 50)
    print("\nStarting application...")
    print("(Close the window to exit)")
    print("=" * 50)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Try to start the app
    app = QApplication(sys.argv)
    window = MainWindow(db_manager)
    window.show()
    print("✅ Application window opened successfully!")
    sys.exit(app.exec())
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
