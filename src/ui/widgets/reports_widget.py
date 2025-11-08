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
from src.database.models import Product, PurchaseOrder, PatientCoupon, MedicalCentre, DistributionLocation
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
        self.report_tabs.addTab(self.create_activity_report_tab(), "📅 Activity Report")
        self.report_tabs.addTab(self.create_summary_report_tab(), "📈 Summary Statistics")
        
        layout.addWidget(self.report_tabs)
    
    def create_stock_report_tab(self) -> QWidget:
        """Create stock report tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("📦 Stock Inventory Report")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        info = QLabel("View current stock levels across all products and purchase orders")
        info.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        generate_btn = QPushButton("🔄 Generate Stock Report")
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
            "Product", "Reference", "Total Ordered", "Remaining", "Used", "Status"
        ])
        
        header = self.stock_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
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
    
    def generate_stock_report(self):
        """Generate stock inventory report."""
        try:
            stock_summary = self.stock_service.get_stock_summary()
            
            self.stock_table.setRowCount(0)
            
            total_products = len(stock_summary)
            total_ordered = sum(item['total_ordered'] for item in stock_summary)
            total_remaining = sum(item['total_remaining'] for item in stock_summary)
            total_used = total_ordered - total_remaining
            
            self.stock_summary_label.setText(
                f"📊 Stock Summary: {total_products} products | "
                f"Total Ordered: {total_ordered} pieces | "
                f"Remaining: {total_remaining} pieces | "
                f"Used: {total_used} pieces"
            )
            
            for item in stock_summary:
                row = self.stock_table.rowCount()
                self.stock_table.insertRow(row)
                
                # Product name
                self.stock_table.setItem(row, 0, QTableWidgetItem(item['product_name']))
                
                # Reference
                self.stock_table.setItem(row, 1, QTableWidgetItem(item['product_reference']))
                
                # Total ordered
                ordered_item = QTableWidgetItem(str(item['total_ordered']))
                ordered_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.stock_table.setItem(row, 2, ordered_item)
                
                # Remaining
                remaining_item = QTableWidgetItem(str(item['total_remaining']))
                remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.stock_table.setItem(row, 3, remaining_item)
                
                # Used
                used_item = QTableWidgetItem(str(item['total_used']))
                used_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.stock_table.setItem(row, 4, used_item)
                
                # Status
                # Calculate remaining percentage (not usage percentage)
                remaining_percentage = ((item['total_remaining'] / item['total_ordered']) * 100) if item['total_ordered'] > 0 else 0
                
                if remaining_percentage == 0:
                    status = "Depleted"
                    color = QColor("#f8d7da")
                    text_color = QColor("#721c24")
                elif remaining_percentage <= 20:
                    status = "Critical"
                    color = QColor("#fff3cd")
                    text_color = QColor("#856404")
                elif remaining_percentage <= 50:
                    status = "Low"
                    color = QColor("#fff3cd")
                    text_color = QColor("#856404")
                else:
                    status = "Healthy"
                    color = QColor("#d4edda")
                    text_color = QColor("#155724")
                
                status_item = QTableWidgetItem(f"{status} ({remaining_percentage:.1f}%)")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setBackground(color)
                status_item.setForeground(text_color)
                self.stock_table.setItem(row, 5, status_item)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate stock report:\n{str(e)}")
    
    def generate_coupon_report(self):
        """Generate coupon distribution report."""
        try:
            # Get filters
            date_from = self.coupon_date_from.date().toPyDate()
            date_to = self.coupon_date_to.date().toPyDate()
            status_filter = self.coupon_status_filter.currentText()
            product_id = self.coupon_product_filter.currentData()
            
            # Get all coupons
            all_coupons = self.db_manager.get_all(PatientCoupon)
            
            # Apply filters
            filtered_coupons = []
            for coupon in all_coupons:
                # Date filter
                if coupon.created_at.date() < date_from or coupon.created_at.date() > date_to:
                    continue
                
                # Status filter
                if status_filter == "Verified" and not coupon.verified:
                    continue
                elif status_filter == "Pending" and coupon.verified:
                    continue
                
                # Product filter
                if product_id and coupon.product_id != product_id:
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
                
                # Date
                self.coupon_table.setItem(row, 0, QTableWidgetItem(
                    coupon.created_at.strftime("%Y-%m-%d %H:%M")
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
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Report exported successfully to:\n{file_path}\n\n"
                f"Total rows: {table.rowCount()}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export report:\n{str(e)}")
