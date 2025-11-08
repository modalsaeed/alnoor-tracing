"""Main application entry point for Alnoor Medical Services Tracking App."""

import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from src.database.db_manager import get_db_manager
from src.ui.main_window import MainWindow


def main():
    """Initialize and run the application."""
    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Alnoor Medical Services")
    app.setOrganizationName("Alnoor Medical Services")
    
    # Set application style
    app.setStyle('Fusion')
    
    try:
        # Initialize database
        db_manager = get_db_manager()
        
        # Create and show main window
        window = MainWindow(db_manager)
        window.show()
        
        # Run application event loop
        sys.exit(app.exec())
        
    except Exception as e:
        # Show error dialog if initialization fails
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("Application Error")
        error_box.setText("Failed to start application")
        error_box.setDetailedText(str(e))
        error_box.exec()
        sys.exit(1)
    finally:
        # Clean up database connection
        if 'db_manager' in locals():
            db_manager.close()


if __name__ == '__main__':
    main()
