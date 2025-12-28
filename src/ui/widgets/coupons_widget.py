from src.utils.model_helpers import get_attr
"""
Coupons Widget - Patient coupon management with verification workflow.

Displays and manages patient coupons with product distribution tracking.
This is the core business functionality linking all entities together.
"""

from typing import Optional
from datetime import datetime
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr
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

from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon, Product, MedicalCentre, DistributionLocation
from src.ui.dialogs.coupon_dialog import CouponDialog
from src.ui.dialogs.verify_coupon_dialog import VerifyCouponDialog
from src.ui.dialogs.grv_reference_dialog import GRVReferenceDialog
from src.utils import Colors, Fonts, Spacing, StyleSheets, IconStyles
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class CouponsWidget(QWidget):
    """Widget for managing patient coupons with verification workflow."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.coupons = []
        # Main layout setup
        layout = QVBoxLayout(self)
        filter_layout = QHBoxLayout()
        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Coupon Ref", "Patient Name", "CPR", "Product", "Quantity", "Medical Centre", "Distribution Location", "Date", "DN Number", "GRV Reference", "Status", "Verification Reference"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # Allow multi-selection
        self.table.doubleClicked.connect(self.edit_coupon)
        self.table.setStyleSheet(StyleSheets.table())
        # Set column resize modes for better visibility
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)   # Coupon Ref
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Patient Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # CPR
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Product
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Quantity
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Medical Centre
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)           # Distribution Location
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # DN Number
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # GRV Reference
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Stretch)          # Verification Reference
        header.setStretchLastSection(True)
        # Only add self.table to the layout after layout is initialized, not here
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by patient, CPR, or verification ref...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)

        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Verified"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)

        # Product filter
        self.product_filter = QComboBox()
        self.product_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.product_filter)

        # Medical Centre filter
        self.centre_filter = QComboBox()
        self.centre_filter.currentIndexChanged.connect(self.apply_filters)
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
        date_layout.addWidget(self.date_from)
        
        date_layout.addWidget(QLabel("to"))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_to)
        
        apply_dates_btn = QPushButton("Apply")
        apply_dates_btn.clicked.connect(self.apply_filters)
        date_layout.addWidget(apply_dates_btn)
        
        clear_dates_btn = QPushButton("Clear Dates")
        clear_dates_btn.clicked.connect(self.clear_date_filters)
        date_layout.addWidget(clear_dates_btn)
        
        date_layout.addWidget(QLabel(" | Sort:"))
        
        self.sort_order = QComboBox()
        self.sort_order.addItem("⬇️ Newest First", "desc")
        self.sort_order.addItem("⬆️ Oldest First", "asc")
        self.sort_order.currentTextChanged.connect(self.apply_filters)
        date_layout.addWidget(self.sort_order)
        
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton(f"{IconStyles.ADD} Add Coupon")
        add_btn.clicked.connect(self.add_coupon)
        add_btn.setStyleSheet(StyleSheets.button_primary(Colors.SUCCESS))
        button_layout.addWidget(add_btn)
        
        bulk_add_btn = QPushButton("📦 Bulk Add")
        bulk_add_btn.setToolTip("Add multiple coupons at once")
        bulk_add_btn.clicked.connect(self.bulk_add_coupons)
        bulk_add_btn.setStyleSheet(StyleSheets.button_primary(Colors.INFO))
        button_layout.addWidget(bulk_add_btn)
        
        verify_btn = QPushButton(f"{IconStyles.VERIFIED} Verify Health Centre Code")
        verify_btn.setToolTip("Verify one or more selected coupons (Ctrl+Click for multiple)")
        verify_btn.clicked.connect(self.verify_coupon)
        verify_btn.setStyleSheet(StyleSheets.button_primary(Colors.PRIMARY))
        button_layout.addWidget(verify_btn)
        
        select_all_btn = QPushButton("☑️ Select All Shown")
        select_all_btn.setToolTip("Select all coupons currently displayed")
        select_all_btn.clicked.connect(self.select_all_shown)
        select_all_btn.setStyleSheet(StyleSheets.button_secondary())
        button_layout.addWidget(select_all_btn)
        
        grv_btn = QPushButton("📄 Add GRV Reference")
        grv_btn.setToolTip("Add Goods Received Voucher reference to verified bundles")
        grv_btn.clicked.connect(self.add_grv_reference)
        grv_btn.setStyleSheet(StyleSheets.button_primary(Colors.SUCCESS))
        button_layout.addWidget(grv_btn)
        
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
        layout.addWidget(self.table)
    
    def load_filter_data(self):
        """Load data for filter dropdowns."""
        try:
            # Load products
            products = self.db_manager.get_all(Product)
            self.products_by_id = {get_id(product): product for product in products}
            self.product_filter.clear()
            self.product_filter.addItem("All Products", None)
            for product in products:
                self.product_filter.addItem(get_name(product), get_id(product))

            # Load medical centres
            centres = self.db_manager.get_all(MedicalCentre)
            self.centres_by_id = {get_id(centre): centre for centre in centres}
            self.centre_filter.clear()
            self.centre_filter.addItem("All Centres", None)
            for centre in centres:
                self.centre_filter.addItem(get_name(centre), get_id(centre))

            # Load distribution locations
            locations = self.db_manager.get_all(DistributionLocation)
            self.locations_by_id = {get_id(location): location for location in locations}
            self.location_filter.clear()
            self.location_filter.addItem("All Locations", None)
            for location in locations:
                self.location_filter.addItem(get_name(location), get_id(location))
                
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
        # Enable date filtering when this is called from Apply button
        self.date_filter_enabled = True
        
        search_text = self.search_input.text().lower() if self.search_input else ""
        status_filter = self.status_filter.currentText() if self.status_filter else "All"
        product_id = self.product_filter.currentData() if self.product_filter else None
        centre_id = self.centre_filter.currentData() if self.centre_filter else None
        location_id = self.location_filter.currentData() if self.location_filter else None
        date_from = self.date_from.date().toPyDate() if self.date_from else None
        date_to = self.date_to.date().toPyDate() if self.date_to else None
        
        self.filtered_coupons = []
        
        for coupon in self.coupons:
            # Search filter (dict/ORM safe)
            patient_name = get_attr(coupon, 'patient_name', '')
            cpr = get_attr(coupon, 'cpr', '')
            verification_ref = get_attr(coupon, 'verification_reference', '')
            coupon_ref = str(get_attr(coupon, 'coupon_reference', ''))
            searchable = f"{patient_name} {cpr} {verification_ref} {coupon_ref}".lower()
            if search_text and search_text not in searchable:
                continue

            # Status filter (dict/ORM safe)
            verified = get_attr(coupon, 'verified', False)
            if status_filter == "Pending" and verified:
                continue
            elif status_filter == "Verified" and not verified:
                continue

            # Product filter (dict/ORM safe)
            coupon_product_id = get_attr(coupon, 'product_id', None)
            if product_id and coupon_product_id != product_id:
                continue

            # Medical Centre filter (dict/ORM safe)
            coupon_centre_id = get_attr(coupon, 'medical_centre_id', None)
            if centre_id and coupon_centre_id != centre_id:
                continue

            # Distribution Location filter (dict/ORM safe)
            coupon_location_id = get_attr(coupon, 'distribution_location_id', None)
            if location_id and coupon_location_id != location_id:
                continue

            # Date filter (only if enabled, dict/ORM safe)
            if self.date_filter_enabled and date_from and date_to:
                coupon_date_val = get_attr(coupon, 'date_received') or get_attr(coupon, 'created_at')
                coupon_date = None
                import datetime as dt
                if isinstance(coupon_date_val, dt.datetime):
                    coupon_date = coupon_date_val.date()
                elif isinstance(coupon_date_val, str):
                    try:
                        coupon_date = dt.datetime.fromisoformat(coupon_date_val).date()
                    except Exception:
                        coupon_date = None
                if coupon_date is None:
                    continue
                if coupon_date < date_from or coupon_date > date_to:
                    continue

            self.filtered_coupons.append(coupon)
        
        self.populate_table()
        self.update_statistics()
    
    def clear_date_filters(self):
        """Clear date range filters to show all coupons."""
        self.date_filter_enabled = False
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.apply_filters()
    
    def populate_table(self):
        """Populate table with filtered coupons."""
        self.table.setRowCount(0)
        
        # Sort coupons by date_received (dict/ORM safe)
        import datetime as dt
        from src.utils.model_helpers import get_attr
        sort_order = self.sort_order.currentData() if hasattr(self, 'sort_order') else "desc"
        def get_sort_date(c):
            val = get_attr(c, 'date_received') or get_attr(c, 'created_at')
            if isinstance(val, dt.datetime):
                return val
            elif isinstance(val, str):
                try:
                    return dt.datetime.fromisoformat(val)
                except Exception:
                    return dt.datetime.min
            return dt.datetime.min
        sorted_coupons = sorted(
            self.filtered_coupons,
            key=get_sort_date,
            reverse=(sort_order == "desc")
        )

        for coupon in sorted_coupons:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # ID
            from src.utils.model_helpers import get_attr
            self.table.setItem(row, 0, QTableWidgetItem(str(get_attr(coupon, 'coupon_reference', '-'))))
            
            # Patient Name (handle None)
            self.table.setItem(row, 1, QTableWidgetItem(get_attr(coupon, 'patient_name', 'N/A')))
            
            # CPR (handle None)
            self.table.setItem(row, 2, QTableWidgetItem(get_attr(coupon, 'cpr', 'N/A')))
            
            # Product (resolve name for dicts)
            product_id = get_attr(coupon, 'product_id', None)
            if isinstance(coupon, dict) and product_id and hasattr(self, 'products_by_id'):
                product = self.products_by_id.get(product_id)
                product_name = get_name(product) if product else 'Unknown'
            else:
                product_name = get_nested_attr(coupon, 'product.name', 'Unknown')
            self.table.setItem(row, 3, QTableWidgetItem(product_name))

            # Quantity
            quantity_item = QTableWidgetItem(f"{get_attr(coupon, 'quantity_pieces', 0)} pcs")
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, quantity_item)

            # Medical Centre (resolve name for dicts)
            centre_id = get_attr(coupon, 'medical_centre_id', None)
            if isinstance(coupon, dict) and centre_id and hasattr(self, 'centres_by_id'):
                centre = self.centres_by_id.get(centre_id)
                centre_name = get_name(centre) if centre else 'Unknown'
            else:
                centre_name = get_nested_attr(coupon, 'medical_centre.name', 'Unknown')
            self.table.setItem(row, 5, QTableWidgetItem(centre_name))

            # Distribution Location (resolve name for dicts)
            location_id = get_attr(coupon, 'distribution_location_id', None)
            if isinstance(coupon, dict) and location_id and hasattr(self, 'locations_by_id'):
                location = self.locations_by_id.get(location_id)
                location_name = get_name(location) if location else 'Unknown'
            else:
                location_name = get_nested_attr(coupon, 'distribution_location.name', 'Unknown')
            self.table.setItem(row, 6, QTableWidgetItem(location_name))
            
            # Date - use date_received (date only, no timestamp), dict/ORM safe
            coupon_date_val = get_attr(coupon, 'date_received') or get_attr(coupon, 'created_at')
            coupon_date = None
            import datetime as dt
            if isinstance(coupon_date_val, dt.datetime):
                coupon_date = coupon_date_val
            elif isinstance(coupon_date_val, str):
                try:
                    coupon_date = dt.datetime.fromisoformat(coupon_date_val)
                except Exception:
                    coupon_date = None
            date_str = coupon_date.strftime("%Y-%m-%d") if coupon_date else "-"
            self.table.setItem(row, 7, QTableWidgetItem(date_str))
            
            # DN Number (dict/ORM safe)
            dn_number = get_attr(coupon, 'delivery_note_number', '-')
            self.table.setItem(row, 8, QTableWidgetItem(dn_number))

            # GRV Reference (dict/ORM safe)
            grv_ref = get_attr(coupon, 'grv_reference', '-')
            grv_item = QTableWidgetItem(grv_ref)
            if grv_ref and grv_ref != '-':
                grv_item.setBackground(QColor(Colors.ALERT_SUCCESS_BG))
                grv_item.setForeground(QColor(Colors.SUCCESS))
            self.table.setItem(row, 9, grv_item)

            # Status (with color coding, dict/ORM safe)
            verified = get_attr(coupon, 'verified', False)
            status_text = f"{IconStyles.VERIFIED} Verified" if verified else f"{IconStyles.PENDING} Pending"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if verified:
                status_item.setBackground(QColor(Colors.ALERT_SUCCESS_BG))
                status_item.setForeground(QColor(Colors.SUCCESS))
            else:
                status_item.setBackground(QColor(Colors.ALERT_WARNING_BG))
                status_item.setForeground(QColor(Colors.WARNING))
            self.table.setItem(row, 10, status_item)

            # Verification Reference (dict/ORM safe)
            ver_ref = get_attr(coupon, 'verification_reference', '-')
            self.table.setItem(row, 11, QTableWidgetItem(ver_ref))
    
    def update_statistics(self):
        """Update statistics label."""
        total = len(self.filtered_coupons)
        verified = sum(1 for c in self.filtered_coupons if get_attr(c, 'verified', False))
        pending = total - verified
        total_quantity = sum(get_attr(c, 'quantity_pieces', 0) for c in self.filtered_coupons)
        self.stats_label.setText(
            f"{IconStyles.DASHBOARD} Total: {total} coupons | "
            f"{IconStyles.VERIFIED} Verified: {verified} | "
            f"{IconStyles.PENDING} Pending: {pending} | "
            f"{IconStyles.PRODUCT} Total Quantity: {total_quantity} pieces"
        )
    
    def add_coupon(self):
        """Open dialog to add a new coupon."""
        dialog = CouponDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_coupons()
    
    def bulk_add_coupons(self):
        """Open dialog to add multiple coupons at once."""
        from src.ui.dialogs.bulk_coupon_dialog import BulkCouponDialog
        
        dialog = BulkCouponDialog(self.db_manager, parent=self)
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
        
        # Cannot edit verified coupons (dict/ORM safe)
        if get_attr(coupon, 'verified', False):
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
    
    def select_all_shown(self):
        """Select all currently displayed coupons in the table."""
        self.table.selectAll()
        QMessageBox.information(
            self,
            "Selection",
            f"Selected all {len(self.filtered_coupons)} shown coupon(s).\n"
            "You can now verify them all at once."
        )
    
    def verify_coupon(self):
        """Open dialog to verify selected coupon(s)."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select one or more coupons to verify.\n\n"
                "Tip: Hold Ctrl to select multiple coupons, or Shift to select a range."
            )
            return
        
        # Get selected coupons
        selected_coupons = [self.filtered_coupons[row.row()] for row in selected_rows]

        # Check if any are already verified (use get_attr for dict/ORM compatibility)
        already_verified = [c for c in selected_coupons if get_attr(c, 'verified', False)]
        if already_verified:
            if len(already_verified) == len(selected_coupons):
                # All selected are verified
                QMessageBox.information(
                    self,
                    "Already Verified",
                    f"All {len(selected_coupons)} selected coupon(s) have already been verified.\n\n"
                    f"Please select unverified coupons to verify."
                )
                return
            else:
                # Some are verified
                reply = QMessageBox.question(
                    self,
                    "Some Already Verified",
                    f"{len(already_verified)} of {len(selected_coupons)} selected coupons are already verified.\n\n"
                    f"Do you want to continue and verify only the unverified ones?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                
                # Filter to only unverified
                selected_coupons = [c for c in selected_coupons if not c.verified]
        
        # Open verification dialog with list of coupons
        dialog = VerifyCouponDialog(self.db_manager, selected_coupons, parent=self)
        if dialog.exec():
            self.load_coupons()
    
    def add_grv_reference(self):
        """Open dialog to add GRV reference to verified bundles."""
        dialog = GRVReferenceDialog(self.db_manager, parent=self)
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
        if get_attr(coupon, 'verified', False):
            reply = QMessageBox.question(
                self,
                "Delete Verified Coupon?",
                f"⚠️ This coupon has been verified and stock has been deducted.\n\n"
                f"Patient: {get_attr(coupon, 'patient_name', '')}\n"
                f"CPR: {get_attr(coupon, 'cpr', '')}\n"
                f"Product: {get_nested_attr(coupon, 'product.name', 'Unknown')}\n"
                f"Quantity: {get_attr(coupon, 'quantity_pieces', 0)} pieces\n"
                f"Verification Ref: {get_attr(coupon, 'verification_reference', '')}\n\n"
                f"Deleting will RESTORE the stock back to the purchase orders.\n\n"
                f"Are you sure you want to delete this verified coupon?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return
            
            # Restore stock before deleting (API/local compatible)
            try:
                from services.stock_service import StockService
                stock_service = StockService(self.db_manager)
                product_id = get_attr(coupon, 'product_id', None)
                quantity = get_attr(coupon, 'quantity_pieces', 0)
                # Patch: Manually fetch purchase orders using db_manager.get_all to avoid session.query
                purchase_orders = self.db_manager.get_all(getattr(self.db_manager, 'PurchaseOrder', None) or __import__('src.database.models', fromlist=['PurchaseOrder']).PurchaseOrder)
                stock_service.restore_stock(product_id, quantity, purchase_orders=purchase_orders)
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
                f"Patient: {get_attr(coupon, 'patient_name', '')}\n"
                f"CPR: {get_attr(coupon, 'cpr', '')}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            # Patch: Use db_manager.delete(PatientCoupon, id) for API mode compatibility
            if hasattr(self.db_manager, 'delete') and hasattr(self.db_manager, 'get_all'):
                # Try to get coupon id (works for both dict and ORM)
                coupon_id = get_attr(coupon, 'id', None)
                if coupon_id is not None:
                    self.db_manager.delete(PatientCoupon, coupon_id)
                else:
                    self.db_manager.delete(coupon)
            else:
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
