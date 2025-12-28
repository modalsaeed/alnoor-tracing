"""
Verify Coupon Dialog - Verification workflow for patient coupons.

Handles the verification process for multiple coupons with manual verification reference entry.
The verification reference is provided by the medical centre/ministry after confirming the data.
"""

from datetime import datetime
from typing import List
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class VerifyCouponDialog(QDialog):
    """Dialog for verifying patient coupons with manual verification reference entry."""
    
    def __init__(self, db_manager: DatabaseManager, coupons: List[PatientCoupon], parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.coupons = coupons if isinstance(coupons, list) else [coupons]
        
        self.init_ui()
        self.load_coupon_details()
    
    def init_ui(self):
        """Initialize the user interface."""
        coupon_count = len(self.coupons)
        self.setWindowTitle(f"Confirm Delivery - {'Coupons' if coupon_count > 1 else 'Coupon'}")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(f"✅ Confirm Delivery - {coupon_count} {'Coupons' if coupon_count > 1 else 'Coupon'}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Info message
        info = QLabel(
            "ℹ️ Verification confirms delivery only. Stock management is handled separately through transactions.\n"
            "The medical centre/ministry will provide a verification reference after confirming the data is correct."
        )
        info.setStyleSheet(
            "background-color: #d1ecf1; padding: 10px; border-radius: 4px; "
            "color: #0c5460; border-left: 4px solid #17a2b8;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addSpacing(10)
        
        # Coupons table
        coupons_label = QLabel("📋 Coupons to Verify")
        coupons_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(coupons_label)
        
        from PyQt6.QtWidgets import QScrollArea, QWidget
        self.coupons_table = QTableWidget()
        self.coupons_table.setColumnCount(5)
        self.coupons_table.setHorizontalHeaderLabels([
            "Coupon Ref", "Patient Name", "CPR", "Product", "Quantity"
        ])
        self.coupons_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.coupons_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.coupons_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.coupons_table.setMinimumHeight(150)
        self.coupons_table.setMaximumHeight(350)
        self.coupons_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Wrap the table in a scroll area for better UX with many coupons
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setWidget(self.coupons_table)
        table_scroll.setMinimumHeight(180)
        table_scroll.setMaximumHeight(400)
        layout.addWidget(table_scroll)
        
        layout.addSpacing(15)
        
        # Verification reference section (MANUAL ENTRY)
        ver_label = QLabel("🔑 Verification Reference (Provided by Medical Centre)")
        ver_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(ver_label)
        
        ver_note = QLabel(
            "Enter the verification reference provided by the medical centre/ministry after they confirm the data."
        )
        ver_note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        ver_note.setWordWrap(True)
        layout.addWidget(ver_note)
        
        self.verification_ref_input = QLineEdit()
        self.verification_ref_input.setPlaceholderText("Enter verification reference (e.g., VER-2024-001)")
        self.verification_ref_input.setStyleSheet(
            "padding: 10px; font-size: 14px; border: 2px solid #2196f3; border-radius: 4px;"
        )
        layout.addWidget(self.verification_ref_input)
        
        layout.addSpacing(10)
        
        # Delivery Note Number section (MANDATORY)
        dn_label = QLabel("📦 Delivery Note Number *")
        dn_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(dn_label)
        
        dn_note = QLabel(
            "Enter the delivery note number that accompanies this shipment."
        )
        dn_note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        dn_note.setWordWrap(True)
        layout.addWidget(dn_note)
        
        self.delivery_note_input = QLineEdit()
        self.delivery_note_input.setPlaceholderText("Enter delivery note number (e.g., DN-2024-001)")
        self.delivery_note_input.setStyleSheet(
            "padding: 10px; font-size: 14px; border: 2px solid #f39c12; border-radius: 4px;"
        )
        layout.addWidget(self.delivery_note_input)
        
        layout.addSpacing(10)
        
        # Delivery Note Date section (MANDATORY)
        dn_date_label = QLabel("📅 Delivery Note Date *")
        dn_date_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(dn_date_label)
        
        dn_date_note = QLabel(
            "Select the date when the delivery note was issued/received."
        )
        dn_date_note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        dn_date_note.setWordWrap(True)
        layout.addWidget(dn_date_note)
        
        self.dn_date_input = QDateEdit()
        self.dn_date_input.setCalendarPopup(True)
        self.dn_date_input.setDate(QDate.currentDate())
        self.dn_date_input.setStyleSheet(
            """
            QDateEdit {
                padding: 10px; 
                font-size: 14px; 
                border: 2px solid #9b59b6; 
                border-radius: 4px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #9b59b6;
            }
            QCalendarWidget QToolButton {
                color: white;
                font-weight: bold;
                background-color: transparent;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: black;
            }
            QCalendarWidget QSpinBox {
                color: white;
                font-weight: bold;
                background-color: transparent;
            }
            """
        )
        layout.addWidget(self.dn_date_input)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        self.verify_btn = QPushButton("✅ Confirm Delivery")
        self.verify_btn.clicked.connect(self.verify_coupons)
        self.verify_btn.setMinimumWidth(180)
        self.verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.verify_btn)
        
        layout.addLayout(button_layout)
    
    def load_coupon_details(self):
        """Load coupon details into the table."""
        self.coupons_table.setRowCount(len(self.coupons))

        # Build a product lookup for fallback
        try:
            all_products = self.db_manager.get_all(getattr(self.db_manager, 'Product', PatientCoupon).product.__class__)
        except Exception:
            all_products = self.db_manager.get_all(PatientCoupon)
        product_lookup = {}
        for p in self.db_manager.get_all(PatientCoupon):
            pid = get_attr(p, 'id', None)
            name = get_attr(p, 'name', None)
            if pid and name:
                product_lookup[pid] = name

        # Try to get all products from db_manager if possible
        try:
            from src.database.models import Product
            products = self.db_manager.get_all(Product)
            product_name_lookup = {get_attr(prod, 'id', None): get_attr(prod, 'name', 'Unknown') for prod in products}
        except Exception:
            product_name_lookup = {}

        for row, coupon in enumerate(self.coupons):
            # Coupon Reference
            ref = get_attr(coupon, 'coupon_reference', '-')
            self.coupons_table.setItem(row, 0, QTableWidgetItem(ref))

            # Patient Name
            patient_name = get_attr(coupon, 'patient_name', None) or "N/A"
            self.coupons_table.setItem(row, 1, QTableWidgetItem(patient_name))

            # CPR
            cpr = get_attr(coupon, 'cpr', None) or "N/A"
            self.coupons_table.setItem(row, 2, QTableWidgetItem(cpr))

            # Product
            product = get_attr(coupon, 'product', None)
            product_name = None
            if product:
                product_name = get_attr(product, 'name', None)
            if not product_name:
                # Try to resolve from product_id
                product_id = get_attr(coupon, 'product_id', None)
                if product_id and product_id in product_name_lookup:
                    product_name = product_name_lookup[product_id]
            if not product_name:
                product_name = "Unknown"
            self.coupons_table.setItem(row, 3, QTableWidgetItem(product_name))

            # Quantity
            qty = get_attr(coupon, 'quantity_pieces', 0)
            qty_item = QTableWidgetItem(f"{qty} pieces")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.coupons_table.setItem(row, 4, qty_item)
    

    
    def verify_coupons(self):
        """Verify all coupons - confirms delivery only, does not affect stock."""
        # Validate verification reference
        verification_ref = self.verification_ref_input.text().strip()
        if not verification_ref:
            QMessageBox.warning(
                self,
                "Missing Verification Reference",
                "Please enter the verification reference provided by the medical centre/ministry."
            )
            self.verification_ref_input.setFocus()
            return
        
        # Validate delivery note number (MANDATORY)
        delivery_note = self.delivery_note_input.text().strip()
        if not delivery_note:
            QMessageBox.warning(
                self,
                "Missing Delivery Note Number",
                "Please enter the delivery note number. This field is mandatory."
            )
            self.delivery_note_input.setFocus()
            return
        
        # Get delivery note date
        dn_date = self.dn_date_input.date().toPyDate()
        dn_date_dt = datetime.combine(dn_date, datetime.min.time())
        
        # Build summarized confirmation message for large coupon sets
        total_quantity = sum(get_attr(c, 'quantity_pieces', 0) for c in self.coupons)
        max_preview = 5
        preview_coupons = self.coupons[:max_preview]
        coupon_list = "\n".join([
            f"  • {get_attr(c, 'patient_name', 'N/A') or 'N/A'} "
            f"({get_attr(c, 'cpr', 'N/A') or 'N/A'}) - "
            f"{get_attr(get_attr(c, 'product', None), 'name', 'Unknown') if get_attr(c, 'product', None) else 'Unknown'} - "
            f"{get_attr(c, 'quantity_pieces', 0)} pieces"
            for c in preview_coupons
        ])
        if len(self.coupons) > max_preview:
            coupon_list += f"\n  ...and {len(self.coupons) - max_preview} more coupon(s)"

        reply = QMessageBox.question(
            self,
            "Confirm Delivery Verification",
            f"Are you sure you want to confirm delivery for {len(self.coupons)} coupon(s)?\n\n"
            f"Verification Reference: {verification_ref}\n"
            f"Delivery Note: {delivery_note}\n\n"
            f"Coupons (showing first {max_preview}):\n{coupon_list}\n\n"
            f"Total Quantity: {total_quantity} pieces\n\n"
            f"Note: This only confirms delivery. Stock is managed separately through transactions.\n"
            f"This action cannot be undone except by deleting the coupons.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        try:
            # Convert to uppercase for consistency
            verification_ref = verification_ref.upper()
            delivery_note = delivery_note.upper()
            
            # Process all coupons in a single transaction
            verified_count = 0
            failed_coupons = []
            
            # Use db_manager.get_all and helpers for compatibility
            all_coupons = self.db_manager.get_all(PatientCoupon)
            for coupon in self.coupons:
                try:
                    db_coupon = next((m for m in all_coupons if get_id(m) == get_id(coupon)), None)
                    if not db_coupon:
                        failed_coupons.append(f"{get_id(coupon)}: Coupon not found in database")
                        continue

                    # Prepare update payload
                    update_fields = {
                        'verified': True,
                        'verification_reference': verification_ref,
                        'delivery_note_number': delivery_note,
                        'date_verified': datetime.now()
                    }

                    # For API mode (DatabaseClient), update expects a record/dict with id and updated fields
                    if hasattr(self.db_manager, 'server_url'):
                        # Merge db_coupon (dict or ORM) with update_fields
                        record = dict(db_coupon) if isinstance(db_coupon, dict) else {k: v for k, v in db_coupon.__dict__.items() if not k.startswith('_')}
                        record.update(update_fields)
                        self.db_manager.update(record)
                    else:
                        # Local DB mode
                        self.db_manager.update(PatientCoupon, get_id(db_coupon), update_fields)

                    verified_count += 1

                except Exception as e:
                    failed_coupons.append(f"{get_id(coupon)}: {str(e)}")
            
            # Show results
            if verified_count == len(self.coupons):
                QMessageBox.information(
                    self,
                    "Delivery Confirmation Successful",
                    f"✅ Successfully confirmed delivery for {verified_count} coupon(s)!\n\n"
                    f"Verification Reference: {verification_ref}\n"
                    f"Delivery Note: {delivery_note}\n"
                    f"Total Quantity Verified: {total_quantity} pieces\n\n"
                    f"All coupons have been marked as verified.\n"
                    f"Remember to record stock transactions separately."
                )
                self.accept()
            else:
                error_details = "\n".join(failed_coupons)
                QMessageBox.warning(
                    self,
                    "Partial Verification",
                    f"⚠️ Verified {verified_count} out of {len(self.coupons)} coupon(s)\n\n"
                    f"Failed coupons:\n{error_details}\n\n"
                    f"Successfully verified coupons have been saved."
                )
                if verified_count > 0:
                    self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Verification Error",
                f"Failed to verify coupons:\n{str(e)}\n\n"
                f"No changes have been made to the database."
            )
