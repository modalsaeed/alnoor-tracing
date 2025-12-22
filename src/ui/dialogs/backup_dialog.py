"""
Backup Dialog - Create and restore database backups.

Allows users to create backups, view existing backups, and restore from backups.
"""

from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.database.db_manager import DatabaseManager


class BackupDialog(QDialog):
    """Dialog for managing database backups."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
        self.load_backups()
        
    def setup_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Database Backup & Restore")
        self.setModal(True)
        self.resize(900, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("💾 Database Backup & Restore")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(title)
        
        # Warning message
        warning = QLabel(
            "⚠️ IMPORTANT: Always create a backup before updating the application or making major changes.\n"
            "Backups are stored in the 'backups' folder next to your database."
        )
        warning.setStyleSheet("""
            background-color: #fff3cd;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        """)
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Database info
        db_info = self.db_manager.get_database_info()
        info_text = QLabel(
            f"📊 Current Database: {Path(db_info['db_path']).name} "
            f"({db_info['db_size_mb']:.2f} MB) | "
            f"Total Coupons: {db_info['coupons_count']} | "
            f"Verified: {db_info['verified_coupons_count']}"
        )
        info_text.setStyleSheet("""
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 8px;
            border-radius: 5px;
            font-weight: bold;
        """)
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        create_backup_btn = QPushButton("➕ Create New Backup")
        create_backup_btn.clicked.connect(self.create_backup)
        create_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(create_backup_btn)
        
        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.clicked.connect(self.load_backups)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        button_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📤 Export Backup")
        export_btn.clicked.connect(self.export_backup)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Backups table
        table_label = QLabel("📁 Available Backups:")
        table_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(table_label)
        
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(4)
        self.backups_table.setHorizontalHeaderLabels([
            "Backup Name", "Created Date", "Size (MB)", "Actions"
        ])
        
        # Configure table
        header = self.backups_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.backups_table.setAlternatingRowColors(True)
        self.backups_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backups_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.backups_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.backups_table)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #95a5a6;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """)
        close_layout.addWidget(close_btn)
        
        layout.addLayout(close_layout)
    
    def load_backups(self):
        """Load and display available backups."""
        try:
            backups = self.db_manager.list_backups()
            
            self.backups_table.setRowCount(len(backups))
            
            for row, backup in enumerate(backups):
                # Backup name
                name_item = QTableWidgetItem(backup['name'])
                self.backups_table.setItem(row, 0, name_item)
                
                # Created date
                date_str = backup['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                date_item = QTableWidgetItem(date_str)
                self.backups_table.setItem(row, 1, date_item)
                
                # Size
                size_item = QTableWidgetItem(f"{backup['size_mb']:.2f}")
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.backups_table.setItem(row, 2, size_item)
                
                # Actions - Create restore button
                restore_btn = QPushButton("🔄 Restore")
                restore_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        padding: 5px 15px;
                        border: none;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
                restore_btn.clicked.connect(lambda checked, path=backup['path']: self.restore_backup(path))
                self.backups_table.setCellWidget(row, 3, restore_btn)
            
            if not backups:
                # Show message if no backups
                self.backups_table.setRowCount(1)
                no_backups_item = QTableWidgetItem("No backups found. Create your first backup!")
                no_backups_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.backups_table.setItem(0, 0, no_backups_item)
                self.backups_table.setSpan(0, 0, 1, 4)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load backups:\n{str(e)}"
            )
    
    def create_backup(self):
        """Create a new database backup."""
        reply = QMessageBox.question(
            self,
            "Create Backup",
            "Create a new backup of the current database?\n\n"
            "This will save a copy of all your data in the backups folder.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                backup_path = self.db_manager.create_backup()
                
                QMessageBox.information(
                    self,
                    "Backup Created",
                    f"✅ Backup created successfully!\n\n"
                    f"Location: {backup_path}\n\n"
                    f"Your data has been safely backed up."
                )
                
                # Refresh the backups list
                self.load_backups()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Backup Error",
                    f"Failed to create backup:\n{str(e)}"
                )
    
    def restore_backup(self, backup_path: str):
        """Restore database from a backup file."""
        reply = QMessageBox.warning(
            self,
            "⚠️ Restore Backup",
            f"Are you sure you want to restore from this backup?\n\n"
            f"⚠️ WARNING: This will REPLACE your current database!\n"
            f"All data entered since this backup was created will be LOST.\n\n"
            f"Backup: {Path(backup_path).name}\n\n"
            f"A backup of your current database will be created before restoring.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.restore_backup(backup_path)
                
                QMessageBox.information(
                    self,
                    "Restore Complete",
                    f"✅ Database restored successfully!\n\n"
                    f"The application will now restart to apply changes."
                )
                
                # Close dialog and signal parent to restart
                self.accept()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Restore Error",
                    f"Failed to restore backup:\n{str(e)}\n\n"
                    f"Your current database has not been modified."
                )
    
    def export_backup(self):
        """Export a backup to a custom location."""
        selected_row = self.backups_table.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a backup to export."
            )
            return
        
        # Get backup path
        backups = self.db_manager.list_backups()
        if selected_row >= len(backups):
            return
        
        backup = backups[selected_row]
        
        # Open file dialog for export location
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Backup",
            f"alnoor_backup_{datetime.now().strftime('%Y%m%d')}.db",
            "Database Files (*.db);;All Files (*.*)"
        )
        
        if export_path:
            try:
                import shutil
                shutil.copy2(backup['path'], export_path)
                
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"✅ Backup exported successfully!\n\n"
                    f"Location: {export_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export backup:\n{str(e)}"
                )
