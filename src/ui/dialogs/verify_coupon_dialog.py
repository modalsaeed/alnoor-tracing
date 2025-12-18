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
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon


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
        
        self.coupons_table = QTableWidget()
        self.coupons_table.setColumnCount(5)
        self.coupons_table.setHorizontalHeaderLabels([
            "Coupon Ref", "Patient Name", "CPR", "Product", "Quantity"
        ])
        self.coupons_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.coupons_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.coupons_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.coupons_table.setMaximumHeight(200)
        layout.addWidget(self.coupons_table)
        
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
        
        for row, coupon in enumerate(self.coupons):
            # Coupon Reference
            self.coupons_table.setItem(row, 0, QTableWidgetItem(coupon.coupon_reference))
            
            # Patient Name
            self.coupons_table.setItem(row, 1, QTableWidgetItem(coupon.patient_name or "N/A"))
            
            # CPR
            self.coupons_table.setItem(row, 2, QTableWidgetItem(coupon.cpr or "N/A"))
            
            # Product
            product_name = coupon.product.name if coupon.product else "Unknown"
            self.coupons_table.setItem(row, 3, QTableWidgetItem(product_name))
            
            # Quantity
            qty_item = QTableWidgetItem(f"{coupon.quantity_pieces} pieces")
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
        
        # Build confirmation message
        coupon_list = "\n".join([
            f"  • {c.patient_name or 'N/A'} ({c.cpr or 'N/A'}) - {c.product.name if c.product else 'Unknown'} - {c.quantity_pieces} pieces"
            for c in self.coupons
        ])
        
        total_quantity = sum(c.quantity_pieces for c in self.coupons)
        
        reply = QMessageBox.question(
            self,
            "Confirm Delivery Verification",
            f"Are you sure you want to confirm delivery for {len(self.coupons)} coupon(s)?\n\n"
            f"Verification Reference: {verification_ref}\n"
            f"Delivery Note: {delivery_note}\n\n"
            f"Coupons:\n{coupon_list}\n\n"
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
            
            # Process each coupon
            verified_count = 0
            failed_coupons = []
            
            for coupon in self.coupons:
                try:
                    # Update coupon verification status and delivery note
                    coupon.verified = True
                    coupon.verification_reference = verification_ref
                    coupon.delivery_note_number = delivery_note
                    coupon.date_verified = datetime.now()
                    
                    self.db_manager.update(coupon)
                    verified_count += 1
                    
                except Exception as e:
                    failed_coupons.append(f"{coupon.coupon_reference}: {str(e)}")
            
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
