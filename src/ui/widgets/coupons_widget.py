"""
Coupons Widget - Patient coupon management with verification workflow.

Displays and manages patient coupons with product distribution tracking.
This is the core business functionality linking all entities together.
"""

from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QLabel,
    QMessageBox,
    QComboBox,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from database import DatabaseManager, PatientCoupon, Product, MedicalCentre, DistributionLocation
from ui.dialogs.coupon_dialog import CouponDialog
from ui.dialogs.verify_coupon_dialog import VerifyCouponDialog
from utils import Colors, Fonts, Spacing, StyleSheets, IconStyles


class CouponsWidget(QWidget):
    """Widget for managing patient coupons with verification workflow."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.coupons = []
        self.filtered_coupons = []
        self.init_ui()
        self.load_coupons()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title and description
        title = QLabel(f"{IconStyles.COUPONS} Patient Coupons Management")
        title.setStyleSheet(f"""
            font-size: {Fonts.SIZE_LARGE}px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: {Spacing.SMALL}px;
        """)
        layout.addWidget(title)
        
        desc = QLabel("Manage patient coupons, verify distributions, and track product usage")
        desc.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            margin-bottom: {Spacing.NORMAL}px;
        """)
        layout.addWidget(desc)
        
        # Search and filter section
        filter_layout = QHBoxLayout()
        
        # Search box
        search_label = QLabel(f"{IconStyles.SEARCH} Search:")
        filter_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by patient name, CPR, or verification reference...")
        self.search_input.textChanged.connect(self.apply_filters)
        self.search_input.setMinimumWidth(300)
        self.search_input.setStyleSheet(StyleSheets.input_field())
        filter_layout.addWidget(self.search_input)
        
        # Verification status filter
        status_label = QLabel("Status:")
        filter_layout.addWidget(status_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Verified"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)
        
        # Product filter
        product_label = QLabel("Product:")
        filter_layout.addWidget(product_label)
        
        self.product_filter = QComboBox()
        self.product_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.product_filter)
        
        # Medical Centre filter
        centre_label = QLabel("Centre:")
        filter_layout.addWidget(centre_label)
        
        self.centre_filter = QComboBox()
        self.centre_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.centre_filter)
        
        # Distribution Location filter
        location_label = QLabel("Location:")
        filter_layout.addWidget(location_label)
        
        self.location_filter = QComboBox()
        self.location_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.location_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Date range filter
        date_layout = QHBoxLayout()
        
        date_label = QLabel("📅 Date Range:")
        date_layout.addWidget(date_label)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.dateChanged.connect(self.apply_filters)
        date_layout.addWidget(self.date_from)
        
        date_layout.addWidget(QLabel("to"))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.apply_filters)
        date_layout.addWidget(self.date_to)
        
        clear_dates_btn = QPushButton("Clear Dates")
        clear_dates_btn.clicked.connect(self.clear_date_filters)
        date_layout.addWidget(clear_dates_btn)
        
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton(f"{IconStyles.ADD} Add Coupon")
        add_btn.clicked.connect(self.add_coupon)
        add_btn.setStyleSheet(StyleSheets.button_primary(Colors.SUCCESS))
        button_layout.addWidget(add_btn)
        
        verify_btn = QPushButton(f"{IconStyles.VERIFIED} Verify Selected")
        verify_btn.clicked.connect(self.verify_coupon)
        verify_btn.setStyleSheet(StyleSheets.button_primary(Colors.PRIMARY))
        button_layout.addWidget(verify_btn)
        
        edit_btn = QPushButton(f"{IconStyles.EDIT} Edit")
        edit_btn.clicked.connect(self.edit_coupon)
        edit_btn.setStyleSheet(StyleSheets.button_secondary())
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton(f"{IconStyles.DELETE} Delete")
        delete_btn.clicked.connect(self.delete_coupon)
        delete_btn.setStyleSheet(StyleSheets.button_primary(Colors.ERROR))
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton(f"{IconStyles.REFRESH} Refresh")
        refresh_btn.clicked.connect(self.load_coupons)
        refresh_btn.setStyleSheet(StyleSheets.button_secondary())
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Statistics bar
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"""
            background-color: {Colors.BG_SECONDARY};
            padding: {Spacing.SMALL}px;
            border-radius: {Spacing.TINY}px;
            color: {Colors.TEXT_PRIMARY};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)
        layout.addWidget(self.stats_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Patient Name", "CPR", "Product", "Quantity",
            "Medical Centre", "Distribution", "Date", "Status", "Verification Ref"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Patient Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # CPR
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Product
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Quantity
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Medical Centre
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Distribution
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)  # Verification Ref
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.edit_coupon)
        self.table.setStyleSheet(StyleSheets.table())
        
        layout.addWidget(self.table)
    
    def load_filter_data(self):
        """Load data for filter dropdowns."""
        try:
            # Load products
            products = self.db_manager.get_all(Product)
            self.product_filter.clear()
            self.product_filter.addItem("All Products", None)
            for product in products:
                self.product_filter.addItem(product.name, product.id)
            
            # Load medical centres
            centres = self.db_manager.get_all(MedicalCentre)
            self.centre_filter.clear()
            self.centre_filter.addItem("All Centres", None)
            for centre in centres:
                self.centre_filter.addItem(centre.name, centre.id)
            
            # Load distribution locations
            locations = self.db_manager.get_all(DistributionLocation)
            self.location_filter.clear()
            self.location_filter.addItem("All Locations", None)
            for location in locations:
                self.location_filter.addItem(location.name, location.id)
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Filter Load Error",
                f"Failed to load filter data:\n{str(e)}"
            )
    
    def load_coupons(self):
        """Load all coupons from database."""
        try:
            self.coupons = self.db_manager.get_all(PatientCoupon)
            self.load_filter_data()
            self.apply_filters()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Coupons",
                f"Failed to load coupons:\n{str(e)}"
            )
    
    def apply_filters(self):
        """Apply current filters to coupon list."""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()
        product_id = self.product_filter.currentData()
        centre_id = self.centre_filter.currentData()
        location_id = self.location_filter.currentData()
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        
        self.filtered_coupons = []
        
        for coupon in self.coupons:
            # Search filter
            if search_text:
                searchable = f"{coupon.patient_name} {coupon.cpr} {coupon.verification_reference or ''}".lower()
                if search_text not in searchable:
                    continue
            
            # Status filter
            if status_filter == "Pending" and coupon.verified:
                continue
            elif status_filter == "Verified" and not coupon.verified:
                continue
            
            # Product filter
            if product_id and coupon.product_id != product_id:
                continue
            
            # Medical Centre filter
            if centre_id and coupon.medical_centre_id != centre_id:
                continue
            
            # Distribution Location filter
            if location_id and coupon.distribution_location_id != location_id:
                continue
            
            # Date filter
            coupon_date = coupon.created_at.date()
            if coupon_date < date_from or coupon_date > date_to:
                continue
            
            self.filtered_coupons.append(coupon)
        
        self.populate_table()
        self.update_statistics()
    
    def clear_date_filters(self):
        """Clear date range filters."""
        self.date_from.setDate(QDate.currentDate().addYears(-10))
        self.date_to.setDate(QDate.currentDate().addYears(10))
    
    def populate_table(self):
        """Populate table with filtered coupons."""
        self.table.setRowCount(0)
        
        for coupon in self.filtered_coupons:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(coupon.id)))
            
            # Patient Name
            self.table.setItem(row, 1, QTableWidgetItem(coupon.patient_name))
            
            # CPR
            self.table.setItem(row, 2, QTableWidgetItem(coupon.cpr))
            
            # Product
            product_name = coupon.product.name if coupon.product else "Unknown"
            self.table.setItem(row, 3, QTableWidgetItem(product_name))
            
            # Quantity
            quantity_item = QTableWidgetItem(f"{coupon.quantity_pieces} pcs")
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, quantity_item)
            
            # Medical Centre
            centre_name = coupon.medical_centre.name if coupon.medical_centre else "Unknown"
            self.table.setItem(row, 5, QTableWidgetItem(centre_name))
            
            # Distribution Location
            location_name = coupon.distribution_location.name if coupon.distribution_location else "Unknown"
            self.table.setItem(row, 6, QTableWidgetItem(location_name))
            
            # Date
            date_str = coupon.created_at.strftime("%Y-%m-%d %H:%M")
            self.table.setItem(row, 7, QTableWidgetItem(date_str))
            
            # Status (with color coding)
            status_text = f"{IconStyles.VERIFIED} Verified" if coupon.verified else f"{IconStyles.PENDING} Pending"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if coupon.verified:
                status_item.setBackground(QColor(Colors.ALERT_SUCCESS_BG))
                status_item.setForeground(QColor(Colors.SUCCESS))
            else:
                status_item.setBackground(QColor(Colors.ALERT_WARNING_BG))
                status_item.setForeground(QColor(Colors.WARNING))
            self.table.setItem(row, 8, status_item)
            
            # Verification Reference
            ver_ref = coupon.verification_reference or "-"
            self.table.setItem(row, 9, QTableWidgetItem(ver_ref))
    
    def update_statistics(self):
        """Update statistics label."""
        total = len(self.filtered_coupons)
        verified = sum(1 for c in self.filtered_coupons if c.verified)
        pending = total - verified
        total_quantity = sum(c.quantity_pieces for c in self.filtered_coupons)
        
        self.stats_label.setText(
            f"{IconStyles.DASHBOARD} Total: {total} coupons | "
            f"{IconStyles.VERIFIED} Verified: {verified} | "
            f"{IconStyles.PENDING} Pending: {pending} | "
            f"{IconStyles.PRODUCTS} Total Quantity: {total_quantity} pieces"
        )
    
    def add_coupon(self):
        """Open dialog to add a new coupon."""
        dialog = CouponDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_coupons()
    
    def edit_coupon(self):
        """Open dialog to edit selected coupon."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a coupon to edit."
            )
            return
        
        coupon = self.filtered_coupons[selected_row]
        
        # Cannot edit verified coupons
        if coupon.verified:
            QMessageBox.warning(
                self,
                "Cannot Edit",
                "Verified coupons cannot be edited.\n"
                "This ensures data integrity for completed distributions."
            )
            return
        
        dialog = CouponDialog(self.db_manager, coupon, parent=self)
        if dialog.exec():
            self.load_coupons()
    
    def verify_coupon(self):
        """Open dialog to verify selected coupon."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a coupon to verify."
            )
            return
        
        coupon = self.filtered_coupons[selected_row]
        
        # Check if already verified
        if coupon.verified:
            QMessageBox.information(
                self,
                "Already Verified",
                f"This coupon was already verified.\n"
                f"Verification Reference: {coupon.verification_reference}\n"
                f"Verified on: {coupon.verified_at.strftime('%Y-%m-%d %H:%M')}"
            )
            return
        
        # Open verification dialog
        dialog = VerifyCouponDialog(self.db_manager, coupon, parent=self)
        if dialog.exec():
            self.load_coupons()
    
    def delete_coupon(self):
        """Delete selected coupon."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a coupon to delete."
            )
            return
        
        coupon = self.filtered_coupons[selected_row]
        
        # Cannot delete verified coupons (would mess up stock tracking)
        if coupon.verified:
            reply = QMessageBox.question(
                self,
                "Delete Verified Coupon?",
                f"⚠️ This coupon has been verified and stock has been deducted.\n\n"
                f"Patient: {coupon.patient_name}\n"
                f"CPR: {coupon.cpr}\n"
                f"Product: {coupon.product.name if coupon.product else 'Unknown'}\n"
                f"Quantity: {coupon.quantity_pieces} pieces\n"
                f"Verification Ref: {coupon.verification_reference}\n\n"
                f"Deleting will RESTORE the stock back to the purchase orders.\n\n"
                f"Are you sure you want to delete this verified coupon?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
            
            # Restore stock before deleting
            try:
                from services.stock_service import StockService
                stock_service = StockService(self.db_manager)
                stock_service.restore_stock(coupon.id)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Stock Restoration Error",
                    f"Failed to restore stock:\n{str(e)}\n\n"
                    f"Coupon will not be deleted to maintain data integrity."
                )
                return
        else:
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete this coupon?\n\n"
                f"Patient: {coupon.patient_name}\n"
                f"CPR: {coupon.cpr}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            self.db_manager.delete(coupon)
            QMessageBox.information(
                self,
                "Success",
                "Coupon deleted successfully!"
            )
            self.load_coupons()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Deleting Coupon",
                f"Failed to delete coupon:\n{str(e)}"
            )
