"""
Reports Widget - Comprehensive reporting and data export functionality.

Provides various reports with filters and CSV export capabilities.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QFrame,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from src.database.db_manager import DatabaseManager
from src.database.models import (
    Product, PurchaseOrder, Purchase, Transaction, PatientCoupon, 
    MedicalCentre, DistributionLocation, Pharmacy
)
from src.services.stock_service import StockService
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class ReportsWidget(QWidget):

    def export_to_csv(self, table_widget, base_filename):
        """
        Export the contents of a QTableWidget to a CSV file.
        Args:
            table_widget: The QTableWidget to export.
            base_filename: The base name for the CSV file.
        """
        from PyQt6.QtWidgets import QFileDialog
        import csv
        from datetime import datetime
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            f"{base_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        if not filename:
            return
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Write headers
                headers = [table_widget.horizontalHeaderItem(col).text() for col in range(table_widget.columnCount())]
                writer.writerow(headers)
                # Write data rows
                for row in range(table_widget.rowCount()):
                    row_data = []
                    for col in range(table_widget.columnCount()):
                        item = table_widget.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export Successful", f"Data exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export CSV:\n{str(e)}")
    """Widget for generating and exporting various reports."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.stock_service = StockService(db_manager)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📊 Reports & Analytics")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        desc = QLabel("Generate comprehensive reports and export data to CSV format")
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 15px;")
        layout.addWidget(desc)
        
        # Create tabbed interface for different report types
        self.report_tabs = QTabWidget()
        
        # Add report tabs
        self.report_tabs.addTab(self.create_stock_report_tab(), "Stock Report")
        self.report_tabs.addTab(self.create_coupon_report_tab(), "🎫 Coupon Report")
        self.report_tabs.addTab(self.create_delivery_note_tab(), "📄 Delivery Notes")
        self.report_tabs.addTab(self.create_activity_report_tab(), "📅 Activity Report")
        self.report_tabs.addTab(self.create_summary_report_tab(), "📈 Summary Statistics")
        
        layout.addWidget(self.report_tabs)
    
    def create_stock_report_tab(self) -> QWidget:
        """Create stock report tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("Stock & Distribution Report")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        info = QLabel("View stock levels, remaining purchases, and pharmacy distributions within a date range")
        info.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Date range filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Date Range:"))
        
        self.stock_date_from = QDateEdit()
        self.stock_date_from.setCalendarPopup(True)
        self.stock_date_from.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.stock_date_from)
        
        filter_layout.addWidget(QLabel("to"))
        
        self.stock_date_to = QDateEdit()
        self.stock_date_to.setCalendarPopup(True)
        self.stock_date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.stock_date_to)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_stock_report)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        controls_layout.addWidget(generate_btn)
        
        export_stock_btn = QPushButton("Export to CSV")
        export_stock_btn.clicked.connect(lambda: self.export_to_csv(self.stock_table, "stock_report"))
        export_stock_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        controls_layout.addWidget(export_stock_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Stock summary info
        self.stock_summary_label = QLabel()
        self.stock_summary_label.setStyleSheet(
            "background-color: #e3f2fd; padding: 10px; border-radius: 4px; "
            "color: #1976d2; font-weight: bold; margin: 10px 0;"
        )
        layout.addWidget(self.stock_summary_label)
        
        # Table
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(6)
        self.stock_table.setHorizontalHeaderLabels([
            "Category", "Item", "Quantity", "Unit Price (BHD)", "Total Price (BHD)", "Notes"
        ])
        
        header_view = self.stock_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.stock_table.setAlternatingRowColors(True)
        layout.addWidget(self.stock_table)
        
        # Auto-generate on load
        self.generate_stock_report()
        
        return widget
    
    def create_coupon_report_tab(self) -> QWidget:
        """Create coupon report tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("🎫 Coupon Distribution Report")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        info = QLabel("Filter and export patient coupon data with verification status")
        info.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Filters
        filter_frame = QFrame()
        filter_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 4px; padding: 10px; }")
        filter_layout = QGridLayout(filter_frame)
        
        # Date range
        filter_layout.addWidget(QLabel("From Date:"), 0, 0)
        self.coupon_date_from = QDateEdit()
        self.coupon_date_from.setCalendarPopup(True)
        self.coupon_date_from.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.coupon_date_from, 0, 1)
        
        filter_layout.addWidget(QLabel("To Date:"), 0, 2)
        self.coupon_date_to = QDateEdit()
        self.coupon_date_to.setCalendarPopup(True)
        self.coupon_date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.coupon_date_to, 0, 3)
        
        # Status filter
        filter_layout.addWidget(QLabel("Status:"), 1, 0)
        self.coupon_status_filter = QComboBox()
        self.coupon_status_filter.addItems(["All", "Verified", "Pending"])
        filter_layout.addWidget(self.coupon_status_filter, 1, 1)
        
        # Product filter
        filter_layout.addWidget(QLabel("Product:"), 1, 2)
        self.coupon_product_filter = QComboBox()
        self.load_product_filter()
        filter_layout.addWidget(self.coupon_product_filter, 1, 3)
        
        # Medical Centre filter
        filter_layout.addWidget(QLabel("Medical Centre:"), 2, 0)
        self.coupon_medical_centre_filter = QComboBox()
        self.load_medical_centre_filter()
        filter_layout.addWidget(self.coupon_medical_centre_filter, 2, 1)
        
        # Distribution Location filter
        filter_layout.addWidget(QLabel("Distribution:"), 2, 2)
        self.coupon_distribution_filter = QComboBox()
        self.load_distribution_filter()
        filter_layout.addWidget(self.coupon_distribution_filter, 2, 3)
        
        layout.addWidget(filter_frame)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        generate_coupon_btn = QPushButton("🔄 Generate Coupon Report")
        generate_coupon_btn.clicked.connect(self.generate_coupon_report)
        generate_coupon_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        controls_layout.addWidget(generate_coupon_btn)
        
        export_coupon_btn = QPushButton("📥 Export to CSV")
        export_coupon_btn.clicked.connect(lambda: self.export_to_csv(self.coupon_table, "coupon_report"))
        export_coupon_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        controls_layout.addWidget(export_coupon_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Coupon summary
        self.coupon_summary_label = QLabel()
        self.coupon_summary_label.setStyleSheet(
            "background-color: #e8f5e9; padding: 10px; border-radius: 4px; "
            "color: #2e7d32; font-weight: bold; margin: 10px 0;"
        )
        layout.addWidget(self.coupon_summary_label)
        
        # Table
        self.coupon_table = QTableWidget()
        self.coupon_table.setColumnCount(9)
        self.coupon_table.setHorizontalHeaderLabels([
            "Date", "Patient", "CPR", "Product", "Quantity", 
            "Medical Centre", "Distribution", "Status", "Verification Ref"
        ])
        
        header = self.coupon_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        
        self.coupon_table.setAlternatingRowColors(True)
        layout.addWidget(self.coupon_table)
        
        return widget
    
    def create_delivery_note_tab(self) -> QWidget:
        """Create delivery note generation tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("📄 Delivery Note Generator")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        info = QLabel(
            "Generate delivery notes from unverified coupons. "
            "Delivery notes are saved as Excel files with auto-incremented reference numbers."
        )
        info.setStyleSheet("color: #7f8c8d; margin-bottom: 15px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Instructions
        instructions_frame = QFrame()
        instructions_frame.setStyleSheet(
            "QFrame { background-color: #e8f5e9; border-radius: 4px; padding: 15px; }"
        )
        instructions_layout = QVBoxLayout(instructions_frame)
        
        instructions_title = QLabel("📋 How to Generate a Delivery Note:")
        instructions_title.setStyleSheet("font-weight: bold; color: #2e7d32; font-size: 14px;")
        instructions_layout.addWidget(instructions_title)
        
        instructions_text = QLabel(
            "1. Click 'Generate Delivery Note' button below\n"
            "2. Select the MOH Health Centre and Distribution Location\n"
            "3. Choose a date range for coupons\n"
            "4. Review the filtered coupons (unverified only)\n"
            "5. Enter pieces per carton\n"
            "6. Click 'Generate' and choose where to save the Excel file\n\n"
            "The delivery note will include:\n"
            "• Auto-incremented delivery note number (DNM-00001)\n"
            "• Health centre and product details\n"
            "• Total pieces and cartons calculation\n"
            "• Current date"
        )
        instructions_text.setStyleSheet("color: #1b5e20; margin-top: 5px; line-height: 1.5;")
        instructions_text.setWordWrap(True)
        instructions_layout.addWidget(instructions_text)
        
        layout.addWidget(instructions_frame)
        
        layout.addSpacing(20)
        
        # Generate button
        generate_button_layout = QHBoxLayout()
        generate_button_layout.addStretch()
        
        generate_dn_btn = QPushButton("📄 Generate Delivery Note")
        generate_dn_btn.clicked.connect(self.open_delivery_note_dialog)
        generate_dn_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        generate_button_layout.addWidget(generate_dn_btn)
        
        dn_copies_btn = QPushButton("📋 DN Copies Report")
        dn_copies_btn.clicked.connect(self.open_dn_copies_report_dialog)
        dn_copies_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        generate_button_layout.addWidget(dn_copies_btn)
        
        generate_button_layout.addStretch()
        
        layout.addLayout(generate_button_layout)
        
        layout.addStretch()
        
        # Recent delivery notes section
        recent_header = QLabel("Recent Delivery Notes")
        recent_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 20px;")
        layout.addWidget(recent_header)
        
        # Table for recent delivery notes
        self.recent_dn_table = QTableWidget()
        self.recent_dn_table.setColumnCount(5)
        self.recent_dn_table.setHorizontalHeaderLabels([
            "Delivery Note #", "Health Centre", "Product", "Total Pieces", "Date Created"
        ])
        
        header_view = self.recent_dn_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.recent_dn_table.setAlternatingRowColors(True)
        self.recent_dn_table.setMaximumHeight(200)
        layout.addWidget(self.recent_dn_table)
        
        # Load recent delivery notes
        self.load_recent_delivery_notes()
        
        return widget
    
    def open_delivery_note_dialog(self):
        """Open the delivery note generation dialog."""
        from src.ui.dialogs.delivery_note_dialog import DeliveryNoteDialog
        
        dialog = DeliveryNoteDialog(self.db_manager, parent=self)
        if dialog.exec():
            # Refresh recent delivery notes list
            self.load_recent_delivery_notes()
    
    def open_dn_copies_report_dialog(self):
        """Open the DN Copies Report dialog."""
        from src.ui.dialogs.dn_copies_report_dialog import DNcopiesReportDialog
        
        dialog = DNcopiesReportDialog(self.db_manager, parent=self)
        dialog.exec()
    
    def load_recent_delivery_notes(self):
        """Load recent delivery notes from the DeliveryNote model."""
        try:
            from datetime import datetime
            all_notes = self.db_manager.get_all(getattr(self.db_manager, 'DeliveryNote', None) or __import__('src.database.models', fromlist=['DeliveryNote']).DeliveryNote)
            # Sort by date_created desc and take first 10
            notes = sorted(all_notes, key=lambda n: get_attr(n, 'date_created', datetime.min), reverse=True)[:10]
            self.recent_dn_table.setRowCount(0)
            for note in notes:
                row = self.recent_dn_table.rowCount()
                self.recent_dn_table.insertRow(row)
                self.recent_dn_table.setItem(row, 0, QTableWidgetItem(get_attr(note, 'delivery_note_number', '-')))
                self.recent_dn_table.setItem(row, 1, QTableWidgetItem(get_attr(note, 'centre_name', '-')))
                self.recent_dn_table.setItem(row, 2, QTableWidgetItem(get_attr(note, 'product_name', '-')))
                self.recent_dn_table.setItem(row, 3, QTableWidgetItem(str(get_attr(note, 'total_pieces', 0))))
                date_val = get_attr(note, 'date_created', None)
                date_str = '-'
                if date_val:
                    if isinstance(date_val, str):
                        try:
                            date_obj = datetime.fromisoformat(date_val)
                            date_str = date_obj.strftime("%d/%m/%Y %H:%M")
                        except Exception:
                            date_str = date_val
                    elif hasattr(date_val, 'strftime'):
                        date_str = date_val.strftime("%d/%m/%Y %H:%M")
                self.recent_dn_table.setItem(row, 4, QTableWidgetItem(date_str))
        except Exception as e:
            print(f"Error loading recent delivery notes: {e}")
    
    def create_activity_report_tab(self) -> QWidget:
        """Create activity report tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("📅 Activity Timeline Report")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        info = QLabel("View chronological activity across all operations")
        info.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Date range filter
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("From:"))
        self.activity_date_from = QDateEdit()
        self.activity_date_from.setCalendarPopup(True)
        self.activity_date_from.setDate(QDate.currentDate().addDays(-30))
        filter_layout.addWidget(self.activity_date_from)
        
        filter_layout.addWidget(QLabel("To:"))
        self.activity_date_to = QDateEdit()
        self.activity_date_to.setCalendarPopup(True)
        self.activity_date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.activity_date_to)
        
        generate_activity_btn = QPushButton("🔄 Generate Activity Report")
        generate_activity_btn.clicked.connect(self.generate_activity_report)
        generate_activity_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        filter_layout.addWidget(generate_activity_btn)
        
        export_activity_btn = QPushButton("📥 Export to CSV")
        export_activity_btn.clicked.connect(lambda: self.export_to_csv(self.activity_table, "activity_report"))
        export_activity_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        filter_layout.addWidget(export_activity_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Activity summary
        self.activity_summary_label = QLabel()
        self.activity_summary_label.setStyleSheet(
            "background-color: #fff3cd; padding: 10px; border-radius: 4px; "
            "color: #856404; font-weight: bold; margin: 10px 0;"
        )
        layout.addWidget(self.activity_summary_label)
        
        # Table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(5)
        self.activity_table.setHorizontalHeaderLabels([
            "Date & Time", "Type", "Entity", "Action", "Details"
        ])
        
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.activity_table.setAlternatingRowColors(True)
        layout.addWidget(self.activity_table)
        
        return widget
    
    def create_summary_report_tab(self) -> QWidget:
        """Create summary statistics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("📈 Summary Statistics")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        info = QLabel("Comprehensive overview of system statistics and trends")
        info.setStyleSheet("color: #7f8c8d; margin-bottom: 15px;")
        layout.addWidget(info)
        
        # Generate button
        generate_summary_btn = QPushButton("🔄 Generate Summary Statistics")
        generate_summary_btn.clicked.connect(self.generate_summary_report)
        generate_summary_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(generate_summary_btn)
        
        layout.addSpacing(15)
        
        # Statistics display area
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 20px;
            }
        """)
        self.summary_layout = QVBoxLayout(self.summary_frame)
        
        placeholder = QLabel("Click 'Generate Summary Statistics' to view comprehensive report")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 40px;")
        self.summary_layout.addWidget(placeholder)
        
        layout.addWidget(self.summary_frame)
        layout.addStretch()
        
        return widget
    
    def load_product_filter(self):
        """Load products into filter dropdown."""
        try:
            products = self.db_manager.get_all(Product)
            self.coupon_product_filter.clear()
            self.coupon_product_filter.addItem("All Products", None)
            for product in products:
                self.coupon_product_filter.addItem(get_name(product), get_id(product))
        except Exception as e:
            print(f"Error loading product filter: {e}")
    
    def load_medical_centre_filter(self):
        """Load medical centres into filter dropdown."""
        try:
            centres = self.db_manager.get_all(MedicalCentre)
            self.coupon_medical_centre_filter.clear()
            self.coupon_medical_centre_filter.addItem("All Centres", None)
            for centre in centres:
                self.coupon_medical_centre_filter.addItem(get_name(centre), get_id(centre))
        except Exception as e:
            print(f"Error loading medical centre filter: {e}")
    
    def load_distribution_filter(self):
        """Load distribution locations into filter dropdown."""
        try:
            locations = self.db_manager.get_all(DistributionLocation)
            self.coupon_distribution_filter.clear()
            self.coupon_distribution_filter.addItem("All Locations", None)
            for location in locations:
                self.coupon_distribution_filter.addItem(get_name(location), get_id(location))
        except Exception as e:
            print(f"Error loading distribution filter: {e}")
    
    def generate_stock_report(self):
        """Generate comprehensive stock and distribution report."""
        try:
            date_from = self.stock_date_from.date().toPyDate()
            date_to = self.stock_date_to.date().toPyDate()
            date_from_dt = datetime.combine(date_from, datetime.min.time())
            date_to_dt = datetime.combine(date_to, datetime.max.time())
            
            self.stock_table.setRowCount(0)
            
            # Section 1: Remaining Local Purchase Orders (non-empty only)
            all_pos = self.db_manager.get_all(PurchaseOrder)
            from src.utils.model_helpers import get_attr, get_nested_attr
            local_pos = [po for po in all_pos if get_attr(po, 'remaining_stock', 0) > 0]
            
            if local_pos:
                self.add_section_header("Local Purchase Orders (Remaining)")
                total_lpo_qty = 0
                total_lpo_price = 0
                for po in local_pos:
                    row = self.stock_table.rowCount()
                    self.stock_table.insertRow(row)
                    self.stock_table.setItem(row, 0, QTableWidgetItem("Local PO"))
                    item_name = f"{get_attr(po, 'po_reference', '')} - {get_nested_attr(po, 'product.name', 'N/A')}"
                    self.stock_table.setItem(row, 1, QTableWidgetItem(item_name))
                    qty = get_attr(po, 'remaining_stock', 0)
                    qty_item = QTableWidgetItem(str(qty))
                    qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.stock_table.setItem(row, 2, qty_item)
                    unit_price = float(get_attr(po, 'unit_price', 0))
                    unit_price_item = QTableWidgetItem(f"{unit_price:.3f}")
                    unit_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    self.stock_table.setItem(row, 3, unit_price_item)
                    remaining_price = unit_price * qty
                    price_item = QTableWidgetItem(f"{remaining_price:.3f}")
                    price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    self.stock_table.setItem(row, 4, price_item)
                    notes = f"Total: {get_attr(po, 'quantity', 0)} | Used: {get_attr(po, 'quantity', 0) - qty}"
                    self.stock_table.setItem(row, 5, QTableWidgetItem(notes))
                    total_lpo_qty += qty
                    total_lpo_price += remaining_price
                # Add subtotal row
                self.add_subtotal_row("Local PO Total", total_lpo_qty, total_lpo_price)
            
            # Section 2: Remaining Supplier Purchases (non-empty only)
            all_purchases = self.db_manager.get_all(Purchase)
            supplier_purchases = [p for p in all_purchases if get_attr(p, 'remaining_stock', 0) > 0]
            
            if supplier_purchases:
                self.add_section_header("Supplier Purchases (Remaining)")
                
                total_sp_qty = 0
                total_sp_price = 0
                
                for purchase in supplier_purchases:
                    row = self.stock_table.rowCount()
                    self.stock_table.insertRow(row)

                    self.stock_table.setItem(row, 0, QTableWidgetItem("Supplier Purchase"))

                    item_name = f"{get_attr(purchase, 'invoice_number', '')} - {get_nested_attr(purchase, 'product.name', 'N/A')}"
                    supplier_name = get_attr(purchase, 'supplier_name', '')
                    if supplier_name:
                        item_name += f" ({supplier_name})"
                    self.stock_table.setItem(row, 1, QTableWidgetItem(item_name))

                    qty = get_attr(purchase, 'remaining_stock', 0)
                    qty_item = QTableWidgetItem(str(qty))
                    qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.stock_table.setItem(row, 2, qty_item)

                    unit_price = float(get_attr(purchase, 'unit_price', 0))
                    unit_price_item = QTableWidgetItem(f"{unit_price:.3f}")
                    unit_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    self.stock_table.setItem(row, 3, unit_price_item)

                    remaining_price = unit_price * qty
                    price_item = QTableWidgetItem(f"{remaining_price:.3f}")
                    price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    self.stock_table.setItem(row, 4, price_item)

                    total_qty = get_attr(purchase, 'quantity', 0)
                    notes = f"Total: {total_qty} | Used: {total_qty - qty}"
                    self.stock_table.setItem(row, 5, QTableWidgetItem(notes))

                    total_sp_qty += qty
                    total_sp_price += remaining_price
                
                # Add subtotal row
                self.add_subtotal_row("Supplier Purchase Total", total_sp_qty, total_sp_price)
            
            # Section 3: Stock Distributed to Pharmacies (within date range)
            all_transactions = self.db_manager.get_all(Transaction)
            transactions = [
                t for t in all_transactions
                if (
                    (lambda d: d if not isinstance(d, str) else datetime.fromisoformat(d))
                    (get_attr(t, 'transaction_date')) >= date_from_dt
                    and
                    (lambda d: d if not isinstance(d, str) else datetime.fromisoformat(d))
                    (get_attr(t, 'transaction_date')) <= date_to_dt
                )
            ]
            
            if transactions:
                self.add_section_header(f"Distributed to Pharmacies ({date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')})")
                
                # Group by pharmacy
                pharmacy_totals = {}
                no_pharmacy_total = 0
                
                # Pre-fetch all pharmacies for lookup to avoid DetachedInstanceError
                pharmacies = self.db_manager.get_all(Pharmacy) if hasattr(self.db_manager, 'get_all') else []
                for txn in transactions:
                    location = get_attr(txn, 'distribution_location')
                    if location:
                        pharmacy_id = get_attr(location, 'pharmacy_id')
                        pharmacy = None
                        # If location is a dict (API mode), use its 'pharmacy' if present, else fetch
                        if isinstance(location, dict):
                            pharmacy = location.get('pharmacy')
                            if not pharmacy and pharmacy_id:
                                pharmacy = next((p for p in pharmacies if get_attr(p, 'id') == pharmacy_id), None)
                                if pharmacy:
                                    location['pharmacy'] = pharmacy
                        else:
                            # ORM object: do NOT access location.pharmacy directly if detached
                            if pharmacy_id:
                                pharmacy = next((p for p in pharmacies if get_attr(p, 'id') == pharmacy_id), None)
                        if pharmacy_id:
                            pharmacy_name = get_name(pharmacy, f"Pharmacy ID {pharmacy_id}")
                            if pharmacy_name not in pharmacy_totals:
                                pharmacy_totals[pharmacy_name] = {
                                    'total_qty': 0,
                                    'locations': {}
                                }
                            loc_name = get_name(location)
                            if loc_name not in pharmacy_totals[pharmacy_name]['locations']:
                                pharmacy_totals[pharmacy_name]['locations'][loc_name] = 0
                            pharmacy_totals[pharmacy_name]['locations'][loc_name] += get_attr(txn, 'quantity', 0)
                            pharmacy_totals[pharmacy_name]['total_qty'] += get_attr(txn, 'quantity', 0)
                        else:
                            # Location without pharmacy - treat as independent
                            loc_name = f"🏪 {get_name(location)} (Independent)"
                            if loc_name not in pharmacy_totals:
                                pharmacy_totals[loc_name] = {
                                    'total_qty': 0,
                                    'locations': {}
                                }
                            pharmacy_totals[loc_name]['total_qty'] += get_attr(txn, 'quantity', 0)
                
                grand_total_qty = 0
                
                # Display pharmacy totals with location breakdown
                for pharmacy_name, data in pharmacy_totals.items():
                    # Pharmacy total row
                    row = self.stock_table.rowCount()
                    self.stock_table.insertRow(row)
                    
                    self.stock_table.setItem(row, 0, QTableWidgetItem("Pharmacy"))
                    
                    pharmacy_item = QTableWidgetItem(pharmacy_name)
                    font = pharmacy_item.font()
                    font.setBold(True)
                    pharmacy_item.setFont(font)
                    self.stock_table.setItem(row, 1, pharmacy_item)
                    
                    qty_item = QTableWidgetItem(str(data['total_qty']))
                    qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    font = qty_item.font()
                    font.setBold(True)
                    qty_item.setFont(font)
                    self.stock_table.setItem(row, 2, qty_item)
                    
                    self.stock_table.setItem(row, 3, QTableWidgetItem("-"))
                    self.stock_table.setItem(row, 4, QTableWidgetItem("-"))
                    self.stock_table.setItem(row, 5, QTableWidgetItem(""))
                    
                    # Set background color for pharmacy rows
                    bg_color = QColor("#e3f2fd")
                    for col in range(6):
                        if self.stock_table.item(row, col):
                            self.stock_table.item(row, col).setBackground(bg_color)
                    
                    # Location breakdown (if it's a real pharmacy with locations)
                    if data['locations']:
                        for loc_name, loc_qty in data['locations'].items():
                            row = self.stock_table.rowCount()
                            self.stock_table.insertRow(row)
                            
                            self.stock_table.setItem(row, 0, QTableWidgetItem("  └─ Location"))
                            self.stock_table.setItem(row, 1, QTableWidgetItem(f"  {loc_name}"))
                            
                            loc_qty_item = QTableWidgetItem(str(loc_qty))
                            loc_qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            self.stock_table.setItem(row, 2, loc_qty_item)
                            
                            self.stock_table.setItem(row, 3, QTableWidgetItem("-"))
                            self.stock_table.setItem(row, 4, QTableWidgetItem("-"))
                            self.stock_table.setItem(row, 5, QTableWidgetItem(""))
                    
                    grand_total_qty += data['total_qty']
                
                # Add grand total row
                self.add_subtotal_row("Total Distributed", grand_total_qty, None)
                
                # Update summary label
                summary_text = f"Report Period: {date_from.strftime('%d/%m/%Y')} to {date_to.strftime('%d/%m/%Y')}"
                if local_pos:
                    summary_text += f" | Local PO Remaining: {total_lpo_qty} units (BHD {total_lpo_price:.3f})"
                if supplier_purchases:
                    summary_text += f" | Supplier Stock Remaining: {total_sp_qty} units (BHD {total_sp_price:.3f})"
                if transactions:
                    summary_text += f" | Distributed: {grand_total_qty} units"
                self.stock_summary_label.setText(summary_text)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate stock report:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def add_section_header(self, title: str):
        """Add a section header row to the table."""
        row = self.stock_table.rowCount()
        self.stock_table.insertRow(row)
        header_item = QTableWidgetItem(title)
        font = header_item.font()
        font.setBold(True)
        font.setPointSize(11)
        header_item.setFont(font)
        header_item.setBackground(QColor("#d3d3d3"))
        self.stock_table.setItem(row, 0, header_item)
        # Merge cells for header (now 6 columns)
        for col in range(1, 6):
            empty_item = QTableWidgetItem("")
            empty_item.setBackground(QColor("#d3d3d3"))
            self.stock_table.setItem(row, col, empty_item)
    
    def add_subtotal_row(self, label: str, quantity: int, price: float = None):
        """Add a subtotal row to the table."""
        row = self.stock_table.rowCount()
        self.stock_table.insertRow(row)
        
        self.stock_table.setItem(row, 0, QTableWidgetItem(""))
        
        label_item = QTableWidgetItem(label)
        font = label_item.font()
        font.setBold(True)
        label_item.setFont(font)
        label_item.setBackground(QColor("#fff3cd"))
        self.stock_table.setItem(row, 1, label_item)
        
        qty_item = QTableWidgetItem(str(quantity))
        qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        font = qty_item.font()
        font.setBold(True)
        qty_item.setFont(font)
        qty_item.setBackground(QColor("#fff3cd"))
        self.stock_table.setItem(row, 2, qty_item)
        
        # Skip unit price column (col 3)
        empty_unit_price = QTableWidgetItem("")
        empty_unit_price.setBackground(QColor("#fff3cd"))
        self.stock_table.setItem(row, 3, empty_unit_price)
        
        if price is not None:
            price_item = QTableWidgetItem(f"{price:.3f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            font = price_item.font()
            font.setBold(True)
            price_item.setFont(font)
            price_item.setBackground(QColor("#fff3cd"))
            self.stock_table.setItem(row, 4, price_item)
        else:
            empty_item = QTableWidgetItem("")
            empty_item.setBackground(QColor("#fff3cd"))
            self.stock_table.setItem(row, 4, empty_item)
        
        # Notes column (col 5)
        empty_notes = QTableWidgetItem("")
        empty_notes.setBackground(QColor("#fff3cd"))
        self.stock_table.setItem(row, 5, empty_notes)
        
        notes_item = QTableWidgetItem("")
        notes_item.setBackground(QColor("#fff3cd"))
        self.stock_table.setItem(row, 4, notes_item)
    
    def generate_coupon_report(self):
        """Generate coupon distribution report."""
        try:
            # Get filters
            date_from = self.coupon_date_from.date().toPyDate()
            date_to = self.coupon_date_to.date().toPyDate()
            status_filter = self.coupon_status_filter.currentText()
            product_id = self.coupon_product_filter.currentData()
            medical_centre_id = self.coupon_medical_centre_filter.currentData()
            distribution_id = self.coupon_distribution_filter.currentData()
            
            # Get all coupons
            all_coupons = self.db_manager.get_all(PatientCoupon)
            
            # Apply filters
            filtered_coupons = []
            from src.utils.model_helpers import get_attr
            for coupon in all_coupons:
                # Date filter - use get_attr for compatibility
                date_val = get_attr(coupon, 'date_received') or get_attr(coupon, 'created_at')
                coupon_date = None
                import datetime as dt
                if isinstance(date_val, dt.datetime):
                    coupon_date = date_val.date()
                elif isinstance(date_val, str):
                    try:
                        coupon_date = dt.datetime.fromisoformat(date_val).date()
                    except Exception:
                        continue
                if coupon_date is None or coupon_date < date_from or coupon_date > date_to:
                    continue

                # Status filter
                verified = get_attr(coupon, 'verified', False)
                if status_filter == "Verified" and not verified:
                    continue
                elif status_filter == "Pending" and verified:
                    continue

                # Product filter
                coupon_product_id = get_attr(coupon, 'product_id', None)
                if product_id and coupon_product_id != product_id:
                    continue

                # Medical Centre filter
                coupon_centre_id = get_attr(coupon, 'medical_centre_id', None)
                if medical_centre_id and coupon_centre_id != medical_centre_id:
                    continue

                # Distribution Location filter
                coupon_location_id = get_attr(coupon, 'distribution_location_id', None)
                if distribution_id and coupon_location_id != distribution_id:
                    continue

                filtered_coupons.append(coupon)
            
            # Populate table
            self.coupon_table.setRowCount(0)
            
            verified_count = sum(1 for c in filtered_coupons if get_attr(c, 'verified', False))
            pending_count = len(filtered_coupons) - verified_count
            total_quantity = sum(get_attr(c, 'quantity_pieces', 0) for c in filtered_coupons)

            self.coupon_summary_label.setText(
                f"Report Summary: {len(filtered_coupons)} coupons | "
                f"Verified: {verified_count} | "
                f"Pending: {pending_count} | "
                f"Total Quantity: {total_quantity} pieces"
            )

            for coupon in filtered_coupons:
                row = self.coupon_table.rowCount()
                self.coupon_table.insertRow(row)

                # Date - use get_attr for compatibility
                date_val = get_attr(coupon, 'date_received') or get_attr(coupon, 'created_at')
                coupon_date = None
                import datetime as dt
                if isinstance(date_val, dt.datetime):
                    coupon_date = date_val
                elif isinstance(date_val, str):
                    try:
                        coupon_date = dt.datetime.fromisoformat(date_val)
                    except Exception:
                        coupon_date = None
                date_str = coupon_date.strftime("%Y-%m-%d") if coupon_date else "-"
                self.coupon_table.setItem(row, 0, QTableWidgetItem(date_str))

                # Patient
                self.coupon_table.setItem(row, 1, QTableWidgetItem(get_attr(coupon, 'patient_name', '')))

                # CPR
                self.coupon_table.setItem(row, 2, QTableWidgetItem(get_attr(coupon, 'cpr', '')))

                # Product
                product_name = get_nested_attr(coupon, 'product.name', 'Unknown')
                self.coupon_table.setItem(row, 3, QTableWidgetItem(product_name))

                # Quantity
                quantity_item = QTableWidgetItem(f"{get_attr(coupon, 'quantity_pieces', 0)} pcs")
                quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.coupon_table.setItem(row, 4, quantity_item)

                # Medical Centre
                centre_name = get_nested_attr(coupon, 'medical_centre.name', 'Unknown')
                self.coupon_table.setItem(row, 5, QTableWidgetItem(centre_name))

                # Distribution Location
                location_name = get_nested_attr(coupon, 'distribution_location.name', 'Unknown')
                self.coupon_table.setItem(row, 6, QTableWidgetItem(location_name))

                # Status
                verified = get_attr(coupon, 'verified', False)
                status_item = QTableWidgetItem("✅ Verified" if verified else "⏳ Pending")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if verified:
                    status_item.setBackground(QColor("#d4edda"))
                    status_item.setForeground(QColor("#155724"))
                else:
                    status_item.setBackground(QColor("#fff3cd"))
                    status_item.setForeground(QColor("#856404"))
                self.coupon_table.setItem(row, 7, status_item)

                # Verification Reference
                ver_ref = get_attr(coupon, 'verification_reference', '-') if verified else "-"
                self.coupon_table.setItem(row, 8, QTableWidgetItem(ver_ref))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate coupon report:\n{str(e)}")
    
    def generate_activity_report(self):
        """Generate activity timeline report."""
        try:
            date_from = self.activity_date_from.date().toPyDate()
            date_to = self.activity_date_to.date().toPyDate()

            # Get all coupons (main activity)
            all_coupons = self.db_manager.get_all(PatientCoupon)

            # Filter by date
            activities = []
            from src.utils.model_helpers import get_attr, get_nested_attr
            for coupon in all_coupons:
                created_at = get_attr(coupon, 'created_at')
                # Parse created_at if it's a string
                if isinstance(created_at, str):
                    try:
                        import datetime as dt
                        created_at = dt.datetime.fromisoformat(created_at)
                    except Exception:
                        continue
                if not created_at:
                    continue
                if hasattr(created_at, 'date') and date_from <= created_at.date() <= date_to:
                    verified = get_attr(coupon, 'verified', False)
                    # Robust product name resolution
                    product = get_attr(coupon, 'product', None)
                    product_name = None
                    if product:
                        product_name = get_name(product)
                    if not product_name or product_name == 'Unknown':
                        product_name = get_nested_attr(coupon, 'product.name', None)
                    if not product_name or product_name == 'Unknown':
                        product_id = get_attr(coupon, 'product_id', None)
                        if product_id:
                            product_name = f"Product ID {product_id}"
                        else:
                            product_name = 'Unknown'
                    activities.append({
                        'datetime': created_at,
                        'type': 'Coupon',
                        'entity': get_attr(coupon, 'patient_name', ''),
                        'action': 'Verified' if verified else 'Created',
                        'details': f"{product_name} - {get_attr(coupon, 'quantity_pieces', 0)} pcs"
                    })

            # Sort by datetime (newest first)
            activities.sort(key=lambda x: x['datetime'], reverse=True)

            # Populate table
            self.activity_table.setRowCount(0)

            self.activity_summary_label.setText(
                f"📊 Activity Summary: {len(activities)} activities between "
                f"{date_from.strftime('%Y-%m-%d')} and {date_to.strftime('%Y-%m-%d')}"
            )

            for activity in activities:
                row = self.activity_table.rowCount()
                self.activity_table.insertRow(row)

                self.activity_table.setItem(row, 0, QTableWidgetItem(
                    activity['datetime'].strftime("%Y-%m-%d %H:%M:%S")
                ))
                self.activity_table.setItem(row, 1, QTableWidgetItem(activity['type']))
                self.activity_table.setItem(row, 2, QTableWidgetItem(activity['entity']))
                self.activity_table.setItem(row, 3, QTableWidgetItem(activity['action']))
                self.activity_table.setItem(row, 4, QTableWidgetItem(activity['details']))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate activity report:\n{str(e)}")
    
    def generate_summary_report(self):
        """Generate comprehensive summary statistics."""
        try:
            # Clear existing widgets
            while self.summary_layout.count() > 0:
                item = self.summary_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Get all data using db_manager.get_all (works for both ORM and API)
            products = self.db_manager.get_all(Product)
            purchase_orders = self.db_manager.get_all(PurchaseOrder)
            coupons = self.db_manager.get_all(PatientCoupon)
            centres = self.db_manager.get_all(MedicalCentre)
            locations = self.db_manager.get_all(DistributionLocation)
            # stock_summary = self.stock_service.get_stock_summary() if hasattr(self, 'stock_service') else None

            from src.utils.model_helpers import get_attr

            # Calculate statistics using get_attr for compatibility
            verified_coupons = [c for c in coupons if get_attr(c, 'verified', False)]
            pending_coupons = [c for c in coupons if not get_attr(c, 'verified', False)]

            total_ordered = sum(get_attr(po, 'quantity', 0) for po in purchase_orders)
            total_remaining = sum(get_attr(po, 'remaining_stock', 0) for po in purchase_orders)
            total_used = total_ordered - total_remaining

            total_coupon_quantity = sum(get_attr(c, 'quantity_pieces', 0) for c in coupons)
            verified_quantity = sum(get_attr(c, 'quantity_pieces', 0) for c in verified_coupons)

            # Avoid division by zero
            percent_remaining = (total_remaining/total_ordered*100) if total_ordered else 0
            percent_used = (total_used/total_ordered*100) if total_ordered else 0
            percent_verified = (len(verified_coupons)/len(coupons)*100) if coupons else 0
            percent_pending = (len(pending_coupons)/len(coupons)*100) if coupons else 0
            avg_quantity_per_coupon = (total_coupon_quantity/len(coupons)) if coupons else 0

            # Create summary display
            summary_html = f"""
            <h2 style=\"color: #2c3e50; margin-bottom: 20px;\">📊 System Summary Statistics</h2>
            <h3 style=\"color: #3498db; margin-top: 20px;\">🏢 System Entities</h3>
            <p><strong>Products:</strong> {len(products)}</p>
            <p><strong>Purchase Orders:</strong> {len(purchase_orders)}</p>
            <p><strong>Medical Centres:</strong> {len(centres)}</p>
            <p><strong>Distribution Locations:</strong> {len(locations)}</p>
            <h3 style=\"color: #3498db; margin-top: 20px;\">📦 Stock Statistics</h3>
            <p><strong>Total Ordered:</strong> {total_ordered:,} pieces</p>
            <p><strong>Remaining Stock:</strong> {total_remaining:,} pieces ({percent_remaining:.1f}%)</p>
            <p><strong>Used Stock:</strong> {total_used:,} pieces ({percent_used:.1f}%)</p>
            <h3 style=\"color: #3498db; margin-top: 20px;\">🎫 Coupon Statistics</h3>
            <p><strong>Total Coupons:</strong> {len(coupons)}</p>
            <p><strong>Verified:</strong> {len(verified_coupons)} ({percent_verified:.1f}%)</p>
            <p><strong>Pending:</strong> {len(pending_coupons)} ({percent_pending:.1f}%)</p>
            <p><strong>Total Distributed Quantity:</strong> {verified_quantity:,} pieces</p>
            <h3 style=\"color: #3498db; margin-top: 20px;\">📈 Performance Metrics</h3>
            <p><strong>Stock Utilization Rate:</strong> {percent_used:.1f}%</p>
            <p><strong>Verification Rate:</strong> {percent_verified:.1f}%</p>
            <p><strong>Average Quantity per Coupon:</strong> {avg_quantity_per_coupon:.1f} pieces</p>
            """

            summary_label = QLabel(summary_html)
            summary_label.setWordWrap(True)
            summary_label.setTextFormat(Qt.TextFormat.RichText)
            summary_label.setStyleSheet("padding: 10px;")
            self.summary_layout.addWidget(summary_label)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate summary report:\n{str(e)}")
