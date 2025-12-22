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


class ReportsWidget(QWidget):
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
        self.report_tabs.addTab(self.create_stock_report_tab(), "📦 Stock Report")
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
        header = QLabel("📦 Stock & Distribution Report")
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
        
        generate_btn = QPushButton("🔄 Generate Report")
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
        
        export_stock_btn = QPushButton("📥 Export to CSV")
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
        """Load recent delivery notes from the database."""
        try:
            with self.db_manager.get_session() as session:
                # Get coupons with delivery notes, grouped by delivery note number
                coupons = session.query(PatientCoupon).filter(
                    PatientCoupon.delivery_note_number.isnot(None)
                ).order_by(PatientCoupon.created_at.desc()).limit(100).all()
                
                # Group by delivery note number
                dn_groups = {}
                for coupon in coupons:
                    dn_num = coupon.delivery_note_number
                    if dn_num not in dn_groups:
                        dn_groups[dn_num] = {
                            'coupons': [],
                            'date': coupon.created_at,
                            'centre': coupon.medical_centre.name if coupon.medical_centre else "N/A",
                            'product': coupon.product.name if coupon.product else "N/A"
                        }
                    dn_groups[dn_num]['coupons'].append(coupon)
                
                # Populate table
                self.recent_dn_table.setRowCount(0)
                for dn_num, data in list(dn_groups.items())[:10]:  # Show last 10
                    row = self.recent_dn_table.rowCount()
                    self.recent_dn_table.insertRow(row)
                    
                    self.recent_dn_table.setItem(row, 0, QTableWidgetItem(dn_num))
                    self.recent_dn_table.setItem(row, 1, QTableWidgetItem(data['centre']))
                    self.recent_dn_table.setItem(row, 2, QTableWidgetItem(data['product']))
                    
                    total_pieces = sum(c.quantity_pieces for c in data['coupons'])
                    self.recent_dn_table.setItem(row, 3, QTableWidgetItem(str(total_pieces)))
                    
                    date_str = data['date'].strftime("%d/%m/%Y %H:%M")
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
                self.coupon_product_filter.addItem(product.name, product.id)
        except Exception as e:
            print(f"Error loading product filter: {e}")
    
    def load_medical_centre_filter(self):
        """Load medical centres into filter dropdown."""
        try:
            centres = self.db_manager.get_all(MedicalCentre)
            self.coupon_medical_centre_filter.clear()
            self.coupon_medical_centre_filter.addItem("All Centres", None)
            for centre in centres:
                self.coupon_medical_centre_filter.addItem(centre.name, centre.id)
        except Exception as e:
            print(f"Error loading medical centre filter: {e}")
    
    def load_distribution_filter(self):
        """Load distribution locations into filter dropdown."""
        try:
            locations = self.db_manager.get_all(DistributionLocation)
            self.coupon_distribution_filter.clear()
            self.coupon_distribution_filter.addItem("All Locations", None)
            for location in locations:
                self.coupon_distribution_filter.addItem(location.name, location.id)
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
            
            with self.db_manager.get_session() as session:
                # Section 1: Remaining Local Purchase Orders (non-empty only)
                local_pos = session.query(PurchaseOrder).filter(
                    PurchaseOrder.remaining_stock > 0
                ).all()
                
                if local_pos:
                    self.add_section_header("📋 Local Purchase Orders (Remaining)")
                    
                    total_lpo_qty = 0
                    total_lpo_price = 0
                    
                    for po in local_pos:
                        row = self.stock_table.rowCount()
                        self.stock_table.insertRow(row)
                        
                        self.stock_table.setItem(row, 0, QTableWidgetItem("Local PO"))
                        
                        item_name = f"{po.po_reference} - {po.product.name if po.product else 'N/A'}"
                        self.stock_table.setItem(row, 1, QTableWidgetItem(item_name))
                        
                        qty_item = QTableWidgetItem(str(po.remaining_stock))
                        qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.stock_table.setItem(row, 2, qty_item)
                        
                        unit_price = float(po.unit_price) if po.unit_price else 0
                        unit_price_item = QTableWidgetItem(f"{unit_price:.3f}")
                        unit_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                        self.stock_table.setItem(row, 3, unit_price_item)
                        
                        remaining_price = unit_price * po.remaining_stock
                        price_item = QTableWidgetItem(f"{remaining_price:.3f}")
                        price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                        self.stock_table.setItem(row, 4, price_item)
                        
                        notes = f"Total: {po.quantity} | Used: {po.quantity - po.remaining_stock}"
                        self.stock_table.setItem(row, 5, QTableWidgetItem(notes))
                        
                        total_lpo_qty += po.remaining_stock
                        total_lpo_price += remaining_price
                    
                    # Add subtotal row
                    self.add_subtotal_row("Local PO Total", total_lpo_qty, total_lpo_price)
                
                # Section 2: Remaining Supplier Purchases (non-empty only)
                supplier_purchases = session.query(Purchase).filter(
                    Purchase.remaining_stock > 0
                ).all()
                
                if supplier_purchases:
                    self.add_section_header("🚚 Supplier Purchases (Remaining)")
                    
                    total_sp_qty = 0
                    total_sp_price = 0
                    
                    for purchase in supplier_purchases:
                        row = self.stock_table.rowCount()
                        self.stock_table.insertRow(row)
                        
                        self.stock_table.setItem(row, 0, QTableWidgetItem("Supplier Purchase"))
                        
                        item_name = f"{purchase.invoice_number} - {purchase.product.name if purchase.product else 'N/A'}"
                        if purchase.supplier_name:
                            item_name += f" ({purchase.supplier_name})"
                        self.stock_table.setItem(row, 1, QTableWidgetItem(item_name))
                        
                        qty_item = QTableWidgetItem(str(purchase.remaining_stock))
                        qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.stock_table.setItem(row, 2, qty_item)
                        
                        unit_price = float(purchase.unit_price)
                        unit_price_item = QTableWidgetItem(f"{unit_price:.3f}")
                        unit_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                        self.stock_table.setItem(row, 3, unit_price_item)
                        
                        remaining_price = unit_price * purchase.remaining_stock
                        price_item = QTableWidgetItem(f"{remaining_price:.3f}")
                        price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                        self.stock_table.setItem(row, 4, price_item)
                        
                        notes = f"Total: {purchase.quantity} | Used: {purchase.quantity - purchase.remaining_stock}"
                        self.stock_table.setItem(row, 5, QTableWidgetItem(notes))
                        
                        total_sp_qty += purchase.remaining_stock
                        total_sp_price += remaining_price
                    
                    # Add subtotal row
                    self.add_subtotal_row("Supplier Purchase Total", total_sp_qty, total_sp_price)
                
                # Section 3: Stock Distributed to Pharmacies (within date range)
                transactions = session.query(Transaction).filter(
                    Transaction.transaction_date >= date_from_dt,
                    Transaction.transaction_date <= date_to_dt
                ).all()
                
                if transactions:
                    self.add_section_header(f"🏥 Distributed to Pharmacies ({date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')})")
                    
                    # Group by pharmacy
                    pharmacy_totals = {}
                    no_pharmacy_total = 0
                    
                    for txn in transactions:
                        location = txn.distribution_location
                        if location:
                            if location.pharmacy_id:
                                pharmacy = location.pharmacy
                                pharmacy_name = pharmacy.name if pharmacy else f"Pharmacy ID {location.pharmacy_id}"
                                
                                if pharmacy_name not in pharmacy_totals:
                                    pharmacy_totals[pharmacy_name] = {
                                        'total_qty': 0,
                                        'locations': {}
                                    }
                                
                                loc_name = location.name
                                if loc_name not in pharmacy_totals[pharmacy_name]['locations']:
                                    pharmacy_totals[pharmacy_name]['locations'][loc_name] = 0
                                
                                pharmacy_totals[pharmacy_name]['locations'][loc_name] += txn.quantity
                                pharmacy_totals[pharmacy_name]['total_qty'] += txn.quantity
                            else:
                                # Location without pharmacy - treat as independent
                                loc_name = f"🏪 {location.name} (Independent)"
                                if loc_name not in pharmacy_totals:
                                    pharmacy_totals[loc_name] = {
                                        'total_qty': 0,
                                        'locations': {}
                                    }
                                pharmacy_totals[loc_name]['total_qty'] += txn.quantity
                    
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
                summary_text = f"📊 Report Period: {date_from.strftime('%d/%m/%Y')} to {date_to.strftime('%d/%m/%Y')}"
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
            for coupon in all_coupons:
                # Date filter - use date_received instead of created_at
                coupon_date = coupon.date_received.date() if coupon.date_received else coupon.created_at.date()
                if coupon_date < date_from or coupon_date > date_to:
                    continue
                
                # Status filter
                if status_filter == "Verified" and not coupon.verified:
                    continue
                elif status_filter == "Pending" and coupon.verified:
                    continue
                
                # Product filter
                if product_id and coupon.product_id != product_id:
                    continue
                
                # Medical Centre filter
                if medical_centre_id and coupon.medical_centre_id != medical_centre_id:
                    continue
                
                # Distribution Location filter
                if distribution_id and coupon.distribution_location_id != distribution_id:
                    continue
                
                filtered_coupons.append(coupon)
            
            # Populate table
            self.coupon_table.setRowCount(0)
            
            verified_count = sum(1 for c in filtered_coupons if c.verified)
            pending_count = len(filtered_coupons) - verified_count
            total_quantity = sum(c.quantity_pieces for c in filtered_coupons)
            
            self.coupon_summary_label.setText(
                f"📊 Report Summary: {len(filtered_coupons)} coupons | "
                f"✅ Verified: {verified_count} | "
                f"⏳ Pending: {pending_count} | "
                f"📦 Total Quantity: {total_quantity} pieces"
            )
            
            for coupon in filtered_coupons:
                row = self.coupon_table.rowCount()
                self.coupon_table.insertRow(row)
                
                # Date - use date_received (date only, no timestamp)
                coupon_date = coupon.date_received if coupon.date_received else coupon.created_at
                self.coupon_table.setItem(row, 0, QTableWidgetItem(
                    coupon_date.strftime("%Y-%m-%d")
                ))
                
                # Patient
                self.coupon_table.setItem(row, 1, QTableWidgetItem(coupon.patient_name))
                
                # CPR
                self.coupon_table.setItem(row, 2, QTableWidgetItem(coupon.cpr))
                
                # Product
                product_name = coupon.product.name if coupon.product else "Unknown"
                self.coupon_table.setItem(row, 3, QTableWidgetItem(product_name))
                
                # Quantity
                quantity_item = QTableWidgetItem(f"{coupon.quantity_pieces} pcs")
                quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.coupon_table.setItem(row, 4, quantity_item)
                
                # Medical Centre
                centre_name = coupon.medical_centre.name if coupon.medical_centre else "Unknown"
                self.coupon_table.setItem(row, 5, QTableWidgetItem(centre_name))
                
                # Distribution Location
                location_name = coupon.distribution_location.name if coupon.distribution_location else "Unknown"
                self.coupon_table.setItem(row, 6, QTableWidgetItem(location_name))
                
                # Status
                status_item = QTableWidgetItem("✅ Verified" if coupon.verified else "⏳ Pending")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if coupon.verified:
                    status_item.setBackground(QColor("#d4edda"))
                    status_item.setForeground(QColor("#155724"))
                else:
                    status_item.setBackground(QColor("#fff3cd"))
                    status_item.setForeground(QColor("#856404"))
                self.coupon_table.setItem(row, 7, status_item)
                
                # Verification Reference
                ver_ref = coupon.verification_reference if coupon.verified else "-"
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
            for coupon in all_coupons:
                if date_from <= coupon.created_at.date() <= date_to:
                    activities.append({
                        'datetime': coupon.created_at,
                        'type': 'Coupon',
                        'entity': coupon.patient_name,
                        'action': 'Verified' if coupon.verified else 'Created',
                        'details': f"{coupon.product.name if coupon.product else 'Unknown'} - {coupon.quantity_pieces} pcs"
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
            
            # Get all data
            products = self.db_manager.get_all(Product)
            purchase_orders = self.db_manager.get_all(PurchaseOrder)
            coupons = self.db_manager.get_all(PatientCoupon)
            centres = self.db_manager.get_all(MedicalCentre)
            locations = self.db_manager.get_all(DistributionLocation)
            stock_summary = self.stock_service.get_stock_summary()
            
            # Calculate statistics
            verified_coupons = [c for c in coupons if c.verified]
            pending_coupons = [c for c in coupons if not c.verified]
            
            total_ordered = sum(po.quantity for po in purchase_orders)
            total_remaining = sum(po.remaining_stock for po in purchase_orders)
            total_used = total_ordered - total_remaining
            
            total_coupon_quantity = sum(c.quantity_pieces for c in coupons)
            verified_quantity = sum(c.quantity_pieces for c in verified_coupons)
            
            # Create summary display
            summary_html = f"""
            <h2 style="color: #2c3e50; margin-bottom: 20px;">📊 System Summary Statistics</h2>
            
            <h3 style="color: #3498db; margin-top: 20px;">🏢 System Entities</h3>
            <p><strong>Products:</strong> {len(products)}</p>
            <p><strong>Purchase Orders:</strong> {len(purchase_orders)}</p>
            <p><strong>Medical Centres:</strong> {len(centres)}</p>
            <p><strong>Distribution Locations:</strong> {len(locations)}</p>
            
            <h3 style="color: #3498db; margin-top: 20px;">📦 Stock Statistics</h3>
            <p><strong>Total Ordered:</strong> {total_ordered:,} pieces</p>
            <p><strong>Remaining Stock:</strong> {total_remaining:,} pieces ({(total_remaining/total_ordered*100):.1f}%)</p>
            <p><strong>Used Stock:</strong> {total_used:,} pieces ({(total_used/total_ordered*100):.1f}%)</p>
            
            <h3 style="color: #3498db; margin-top: 20px;">🎫 Coupon Statistics</h3>
            <p><strong>Total Coupons:</strong> {len(coupons)}</p>
            <p><strong>Verified:</strong> {len(verified_coupons)} ({(len(verified_coupons)/len(coupons)*100):.1f}%)</p>
            <p><strong>Pending:</strong> {len(pending_coupons)} ({(len(pending_coupons)/len(coupons)*100):.1f}%)</p>
            <p><strong>Total Distributed Quantity:</strong> {verified_quantity:,} pieces</p>
            
            <h3 style="color: #3498db; margin-top: 20px;">📈 Performance Metrics</h3>
            <p><strong>Stock Utilization Rate:</strong> {(total_used/total_ordered*100):.1f}%</p>
            <p><strong>Verification Rate:</strong> {(len(verified_coupons)/len(coupons)*100):.1f}%</p>
            <p><strong>Average Quantity per Coupon:</strong> {(total_coupon_quantity/len(coupons)):.1f} pieces</p>
            """
            
            summary_label = QLabel(summary_html)
            summary_label.setWordWrap(True)
            summary_label.setTextFormat(Qt.TextFormat.RichText)
            summary_label.setStyleSheet("padding: 10px;")
            self.summary_layout.addWidget(summary_label)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate summary report:\n{str(e)}")
    
    def export_to_csv(self, table: QTableWidget, report_name: str):
        """Export table data to CSV file."""
        if table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No data available to export.\nPlease generate a report first.")
            return
        
        try:
            # Get file path from user
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"{report_name}_{timestamp}.csv"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export to CSV",
                str(Path.home() / "Downloads" / default_filename),
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            # Write CSV
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write header
                headers = []
                for col in range(table.columnCount()):
                    headers.append(table.horizontalHeaderItem(col).text())
                f.write(','.join(f'"{h}"' for h in headers) + '\n')
                
                # Write data
                for row in range(table.rowCount()):
                    row_data = []
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item:
                            # Clean up data (remove emojis for CSV)
                            text = item.text().replace('✅', 'Verified').replace('⏳', 'Pending')
                            row_data.append(f'"{text}"')
                        else:
                            row_data.append('""')
                    f.write(','.join(row_data) + '\n')
                
                # Add summary for coupon report
                if report_name == "coupon_report" and hasattr(self, 'coupon_summary_label'):
                    summary_text = self.coupon_summary_label.text()
                    # Remove emojis for CSV
                    summary_text = summary_text.replace('📊', '').replace('✅', '').replace('⏳', '').replace('📦', '')
                    f.write('\n')
                    f.write(f'"{summary_text}"\n')
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Report exported successfully to:\n{file_path}\n\n"
                f"Total rows: {table.rowCount()}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export report:\n{str(e)}")
