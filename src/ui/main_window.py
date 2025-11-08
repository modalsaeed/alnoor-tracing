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
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

from database import DatabaseManager
from ui.widgets.products_widget import ProductsWidget
from ui.widgets.distribution_locations_widget import DistributionLocationsWidget
from ui.widgets.medical_centres_widget import MedicalCentresWidget
from ui.widgets.purchase_orders_widget import PurchaseOrdersWidget


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Alnoor Medical Services - Database Tracking System")
        self.setMinimumSize(1200, 800)
        
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
        
        backup_action = QAction('&Backup Database', self)
        backup_action.setShortcut('Ctrl+B')
        backup_action.triggered.connect(self.backup_database)
        file_menu.addAction(backup_action)
        
        restore_action = QAction('&Restore Database', self)
        restore_action.triggered.connect(self.restore_database)
        file_menu.addAction(restore_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
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
        
        # Add tabs with actual widgets
        self.tabs.addTab(self.create_placeholder_tab("Dashboard"), "📊 Dashboard")
        
        # Purchase Orders tab - actual widget
        self.purchase_orders_widget = PurchaseOrdersWidget(self.db_manager)
        self.tabs.addTab(self.purchase_orders_widget, "📦 Purchase Orders")
        
        # Products tab - actual widget
        self.products_widget = ProductsWidget(self.db_manager)
        self.tabs.addTab(self.products_widget, "🏷️ Products")
        
        # Distribution Locations tab - actual widget
        self.distribution_widget = DistributionLocationsWidget(self.db_manager)
        self.tabs.addTab(self.distribution_widget, "📍 Distribution")
        
        # Medical Centres tab - actual widget
        self.medical_centres_widget = MedicalCentresWidget(self.db_manager)
        self.tabs.addTab(self.medical_centres_widget, "🏥 Medical Centres")
        
        self.tabs.addTab(self.create_placeholder_tab("Coupons"), "🎫 Coupons")
        self.tabs.addTab(self.create_placeholder_tab("Reports"), "📄 Reports")
        
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
            db_info = self.db_manager.get_database_info()
            status_text = (
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
        """Center window on screen."""
        from PyQt6.QtGui import QScreen
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def backup_database(self):
        """Create database backup."""
        try:
            backup_path = self.db_manager.create_backup()
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Backup Successful",
                f"Database backed up successfully to:\n{backup_path}"
            )
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"Failed to create backup:\n{str(e)}"
            )
    
    def restore_database(self):
        """Restore database from backup."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        backup_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            "",
            "Database Files (*.db)"
        )
        
        if backup_file:
            reply = QMessageBox.question(
                self,
                "Confirm Restore",
                "Are you sure you want to restore from this backup?\n"
                "Current database will be backed up first.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.db_manager.restore_backup(backup_file)
                    QMessageBox.information(
                        self,
                        "Restore Successful",
                        "Database restored successfully.\nPlease restart the application."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Restore Failed",
                        f"Failed to restore backup:\n{str(e)}"
                    )
    
    def show_about(self):
        """Show about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About Alnoor Medical Services",
            "<h2>Alnoor Medical Services</h2>"
            "<p>Database Tracking System</p>"
            "<p>Version 1.0.0</p>"
            "<p>Copyright © 2025 Alnoor Medical Services</p>"
            "<p>All rights reserved.</p>"
        )
    
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
