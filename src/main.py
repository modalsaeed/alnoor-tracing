"""Main application entry point for Alnoor Medical Services Tracking App."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from src.database.db_manager import get_db_manager, get_connection_debug_info
from src.ui.main_window import MainWindow


def should_show_debug_popup():
    """Check if debug popup should be shown on startup."""
    import configparser
    config_path = Path(__file__).parent.parent / 'config.ini'
    
    if config_path.exists():
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        if 'debug' in config:
            return config['debug'].get('show_connection_debug', 'true').lower() == 'true'
    return True  # Default: show debug info


def main():
    """Initialize and run the application."""
    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Alnoor Medical Services")
    app.setOrganizationName("Alnoor Medical Services")
    
    # Set application style
    app.setStyle('Fusion')
    
    import signal
    db_manager = None
    def handle_exit(*args):
        nonlocal db_manager
        if db_manager is not None:
            db_manager.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    try:
        # Initialize database
        db_manager = get_db_manager()

        # Show connection debug info on startup (if enabled in config)
        if should_show_debug_popup():
            debug_info = get_connection_debug_info()
            if debug_info:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Connection Status")
                msg.setText("Application Startup - Connection Debug Info")
                msg.setInformativeText("\n".join(debug_info))
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()

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
        if db_manager is not None:
            db_manager.close()


if __name__ == '__main__':
    main()
