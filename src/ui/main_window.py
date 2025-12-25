"""Main window for Alnoor Medical Services Tracking App."""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QStatusBar,
    QPushButton,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

from src.database.db_manager import DatabaseManager
from src.ui.widgets.dashboard_widget import DashboardWidget
from src.ui.widgets.products_widget import ProductsWidget
from src.ui.widgets.distribution_locations_widget import DistributionLocationsWidget
from src.ui.widgets.pharmacies_widget import PharmaciesWidget
from src.ui.widgets.medical_centres_widget import MedicalCentresWidget
from src.ui.widgets.purchase_orders_widget import PurchaseOrdersWidget
from src.ui.widgets.purchases_widget import PurchasesWidget
from src.ui.widgets.coupons_widget import CouponsWidget
from src.ui.widgets.transactions_widget import TransactionsWidget
from src.ui.widgets.reports_widget import ReportsWidget


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Determine connection mode
        connection_mode = self.get_connection_mode()
        window_title = f"Alnoor Medical Services - Database Tracking System [{connection_mode}]"
        self.setWindowTitle(window_title)
        self.setMinimumSize(1024, 700)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main content area
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()
        
        # Center window on screen
        self.center_window()
    
    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        backup_action = QAction('💾 &Backup Database', self)
        backup_action.setShortcut('Ctrl+B')
        backup_action.triggered.connect(self.backup_database)
        file_menu.addAction(backup_action)
        
        restore_action = QAction('🔄 &Restore Database', self)
        restore_action.triggered.connect(self.restore_database)
        file_menu.addAction(restore_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        debug_log_action = QAction('📝 Show Debug Log Location', self)
        debug_log_action.triggered.connect(self.show_debug_log_location)
        help_menu.addAction(debug_log_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        undo_verification_action = QAction('⏮️ &Undo Verification', self)
        undo_verification_action.setShortcut('Ctrl+Z')
        undo_verification_action.triggered.connect(self.undo_verification)
        tools_menu.addAction(undo_verification_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_main_content(self):
        """Create main tabbed content area."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Connect tab change event to refresh handler
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Add tabs in new order
        # Dashboard tab
        self.dashboard_widget = DashboardWidget(self.db_manager)
        self.tabs.addTab(self.dashboard_widget, "📊 Dashboard")
        
        # Products tab
        self.products_widget = ProductsWidget(self.db_manager)
        self.tabs.addTab(self.products_widget, "🏷️ Products")

        # Pharmacies tab
        self.pharmacies_widget = PharmaciesWidget(self.db_manager)
        self.tabs.addTab(self.pharmacies_widget, "💊 Pharmacies")

        # Distribution Locations tab
        self.distribution_widget = DistributionLocationsWidget(self.db_manager)
        self.tabs.addTab(self.distribution_widget, "📍 Distribution")

        # Medical Centres tab
        self.medical_centres_widget = MedicalCentresWidget(self.db_manager)
        self.tabs.addTab(self.medical_centres_widget, "🏥 MOH Health Centres")

        # Local Purchase Orders tab
        self.purchase_orders_widget = PurchaseOrdersWidget(self.db_manager)
        self.tabs.addTab(self.purchase_orders_widget, "📋 Local Purchase Order")

        # Supplier Purchases tab
        self.purchases_widget = PurchasesWidget(self.db_manager)
        self.tabs.addTab(self.purchases_widget, "🛒 Supplier Purchase")

        # Transactions tab
        self.transactions_widget = TransactionsWidget(self.db_manager)
        self.tabs.addTab(self.transactions_widget, "🔄 Transactions")

        # Coupons tab
        self.coupons_widget = CouponsWidget(self.db_manager)
        self.tabs.addTab(self.coupons_widget, "🎫 Coupons")

        # Reports tab
        self.reports_widget = ReportsWidget(self.db_manager)
        self.tabs.addTab(self.reports_widget, "📄 Reports")
        
        layout.addWidget(self.tabs)
    
    def create_placeholder_tab(self, title: str) -> QWidget:
        """Create a placeholder tab (temporary)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(f"{title} Module")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #666;")
        
        info_label = QLabel("Coming soon...")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 14px; color: #999;")
        
        layout.addStretch()
        layout.addWidget(label)
        layout.addWidget(info_label)
        layout.addStretch()
        
        return widget
    
    def get_connection_mode(self):
        """Detect if running in local or client mode."""
        # Check if db_manager is a DatabaseClient (API mode)
        try:
            from src.database.db_client import DatabaseClient
            if isinstance(self.db_manager, DatabaseClient):
                return f"API Client: {self.db_manager.server_url}"
        except ImportError:
            pass
        return "Local Database"
    
    def create_status_bar(self):
        """Create status bar with database info."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Update status periodically
        self.update_status()
        
        # Set up timer to update status every 30 seconds
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(30000)  # 30 seconds
    
    def update_status(self):
        """Update status bar with current database info."""
        try:
            # Add connection mode indicator
            connection_mode = self.get_connection_mode()
            mode_indicator = "🌐 API" if "API Client" in connection_mode else "💾 Local"
            
            db_info = self.db_manager.get_database_info()
            status_text = (
                f"{mode_indicator} | "
                f"Products: {db_info['products_count']} | "
                f"POs: {db_info['purchase_orders_count']} | "
                f"Coupons: {db_info['coupons_count']} "
                f"({db_info['verified_coupons_count']} verified) | "
                f"DB Size: {db_info['db_size_mb']:.2f} MB"
            )
            self.status_bar.showMessage(status_text)
        except Exception as e:
            self.status_bar.showMessage(f"Error updating status: {str(e)}")
    
    def center_window(self):
        """Center window on screen and resize to fit if needed."""
        from PyQt6.QtGui import QScreen
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        
        # Calculate desired size (80% of screen or minimum size, whichever is larger)
        desired_width = max(self.minimumWidth(), int(screen.width() * 0.8))
        desired_height = max(self.minimumHeight(), int(screen.height() * 0.85))
        
        # Don't exceed screen size
        final_width = min(desired_width, screen.width())
        final_height = min(desired_height, screen.height())
        
        # Resize window
        self.resize(final_width, final_height)
        
        # Center on screen
        x = (screen.width() - final_width) // 2
        y = (screen.height() - final_height) // 2
        self.move(x, y)
    
    def backup_database(self):
        """Open backup dialog."""
        from src.ui.dialogs.backup_dialog import BackupDialog
        
        dialog = BackupDialog(self.db_manager, self)
        dialog.exec()
    
    def restore_database(self):
        """Open backup dialog for restore."""
        from src.ui.dialogs.backup_dialog import BackupDialog
        
        dialog = BackupDialog(self.db_manager, self)
        dialog.exec()
    
    def undo_verification(self):
        """Open undo verification dialog."""
        from src.ui.dialogs.undo_verification_dialog import UndoVerificationDialog
        
        dialog = UndoVerificationDialog(self.db_manager, self)
        if dialog.exec():
            # Refresh coupons tab if it exists
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if hasattr(widget, 'load_coupons'):
                    widget.load_coupons()
                    break
    
    def show_about(self):
        """Show about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About Alnoor Medical Services",
            "<h2>Alnoor Medical Services</h2>"
            "<p>Database Tracking System</p>"
            "<p>Version 1.0.3</p>"
            "<p>Copyright © 2025 Alnoor Medical Services</p>"
            "<p>All rights reserved.</p>"
        )
    
    def on_tab_changed(self, index):
        """Handle tab change event - refresh current tab data."""
        if index < 0:
            return
        
        # Get the current widget
        current_widget = self.tabs.widget(index)
        
        # Call refresh/load method if available
        if hasattr(current_widget, 'load_data'):
            current_widget.load_data()
        elif hasattr(current_widget, 'refresh'):
            current_widget.refresh()
        elif hasattr(current_widget, 'load_coupons'):
            current_widget.load_coupons()
        elif hasattr(current_widget, 'load_transactions'):
            current_widget.load_transactions()
        elif hasattr(current_widget, 'load_purchase_orders'):
            current_widget.load_purchase_orders()
        elif hasattr(current_widget, 'load_products'):
            current_widget.load_products()
        elif hasattr(current_widget, 'load_medical_centres'):
            current_widget.load_medical_centres()
        elif hasattr(current_widget, 'load_distribution_locations'):
            current_widget.load_distribution_locations()
    
    def show_debug_log_location(self):
        """Show the location of the debug log file."""
        from PyQt6.QtWidgets import QMessageBox
        import os
        import sys
        from pathlib import Path
        import tempfile
        
        # Use EXACT same logic as db_manager.py
        try:
            if getattr(sys, 'frozen', False):
                # Installed app - use LocalAppData
                app_data = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
                log_dir = app_data / 'Alnoor Medical Services' / 'database'
            else:
                # Development mode
                log_dir = Path(__file__).parent.parent.parent / 'logs'
            
            log_path = log_dir / 'connection_debug.log'
            
            # If file doesn't exist there, check temp directory fallback
            if not log_path.exists():
                log_path = Path(tempfile.gettempdir()) / 'alnoor_connection_debug.log'
        except:
            log_path = Path(tempfile.gettempdir()) / 'alnoor_connection_debug.log'
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Debug Log Location")
        msg.setText("Connection debug log file location:")
        msg.setInformativeText(str(log_path.absolute()) + 
                              ("\n\n✅ File exists" if log_path.exists() else "\n\n⚠️ File not created yet"))
        msg.setDetailedText(
            "This log file contains information about:\n"
            "- Config file location\n"
            "- Connection mode (Local or API Client)\n"
            "- Server URL (if in client mode)\n"
            "\nYou can open this folder in File Explorer by copying the path."
        )
        
        # Add button to open folder
        open_folder_btn = msg.addButton("Open Folder", QMessageBox.ButtonRole.ActionRole)
        msg.addButton(QMessageBox.StandardButton.Ok)
        
        msg.exec()
        
        if msg.clickedButton() == open_folder_btn:
            import subprocess
            folder = log_path.parent
            if folder.exists():
                subprocess.run(['explorer', str(folder)])
    
    def closeEvent(self, event):
        """Handle window close event."""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            'Exit Application',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Stop status timer
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            event.accept()
        else:
            event.ignore()
