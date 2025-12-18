"""
GRV Reference Dialog - Add GRV (Goods Received Voucher) references to verified bundles.

Allows users to search for verified coupons by verification code or delivery note number,
then assign a GRV reference to the bundle.
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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon


class GRVReferenceDialog(QDialog):
    """Dialog for adding GRV references to verified coupon bundles."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.found_coupons = []
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Add GRV Reference")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📋 Add GRV Reference to Verified Bundle")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Info message
        info = QLabel(
            "ℹ️ Enter the verification code to find all coupons in that verified bundle, "
            "then assign a GRV reference. The verification code is already linked to the delivery note number."
        )
        info.setStyleSheet(
            "background-color: #d1ecf1; padding: 10px; border-radius: 4px; "
            "color: #0c5460; border-left: 4px solid #17a2b8;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addSpacing(15)
        
        # Search section
        search_label = QLabel("🔍 Search for Verified Bundle")
        search_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(search_label)
        
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Verification Code:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter verification code (e.g., VER-2024-001)...")
        self.search_input.returnPressed.connect(self.search_coupons)
        search_layout.addWidget(self.search_input, 1)
        
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self.search_coupons)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        layout.addSpacing(15)
        
        # Results table
        results_label = QLabel("📦 Found Coupons")
        results_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Coupon Ref", "Patient Name", "Product", "Quantity",
            "Verification Code", "Delivery Note", "Current GRV"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.results_table)
        
        # Summary label
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(
            "background-color: #f8f9fa; padding: 10px; border-radius: 4px; "
            "font-weight: bold; color: #495057;"
        )
        self.summary_label.hide()
        layout.addWidget(self.summary_label)
        
        layout.addSpacing(15)
        
        # GRV Reference input section
        grv_label = QLabel("📄 GRV Reference Number")
        grv_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(grv_label)
        
        grv_note = QLabel(
            "Enter the Goods Received Voucher (GRV) reference number for this bundle."
        )
        grv_note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(grv_note)
        
        self.grv_input = QLineEdit()
        self.grv_input.setPlaceholderText("Enter GRV reference (e.g., GRV-2024-001)")
        self.grv_input.setStyleSheet(
            "padding: 10px; font-size: 14px; border: 2px solid #28a745; border-radius: 4px;"
        )
        layout.addWidget(self.grv_input)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("💾 Save GRV Reference")
        self.save_btn.clicked.connect(self.save_grv_reference)
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumWidth(180)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover:enabled {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def search_coupons(self):
        """Search for verified coupons by verification code."""
        search_term = self.search_input.text().strip().upper()
        
        if not search_term:
            QMessageBox.warning(
                self,
                "Empty Search",
                "Please enter a verification code to search."
            )
            return
        
        try:
            # Get all verified coupons with matching verification code
            all_coupons = self.db_manager.get_all(PatientCoupon)
            
            # Filter by verification code only
            self.found_coupons = [
                c for c in all_coupons
                if c.verified and c.verification_reference and c.verification_reference.upper() == search_term
            ]
            
            if not self.found_coupons:
                QMessageBox.information(
                    self,
                    "No Results",
                    f"No verified coupons found with verification code: {search_term}\n\n"
                    f"Please check:\n"
                    f"• The verification code is correct\n"
                    f"• The coupons have been verified\n"
                    f"• The verification code was entered correctly during verification"
                )
                self.results_table.setRowCount(0)
                self.summary_label.hide()
                self.save_btn.setEnabled(False)
                return
            
            # Get delivery note from first coupon (all in bundle should have same)
            delivery_note = self.found_coupons[0].delivery_note_number or "N/A"
            
            # Populate results table
            self.results_table.setRowCount(len(self.found_coupons))
            
            total_quantity = 0
            
            for row, coupon in enumerate(self.found_coupons):
                # Coupon Reference
                self.results_table.setItem(row, 0, QTableWidgetItem(coupon.coupon_reference))
                
                # Patient Name
                self.results_table.setItem(row, 1, QTableWidgetItem(coupon.patient_name or "N/A"))
                
                # Product
                product_name = coupon.product.name if coupon.product else "Unknown"
                self.results_table.setItem(row, 2, QTableWidgetItem(product_name))
                
                # Quantity
                qty_item = QTableWidgetItem(f"{coupon.quantity_pieces}")
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(row, 3, qty_item)
                total_quantity += coupon.quantity_pieces
                
                # Verification Code
                self.results_table.setItem(row, 4, QTableWidgetItem(coupon.verification_reference or "N/A"))
                
                # Delivery Note
                self.results_table.setItem(row, 5, QTableWidgetItem(coupon.delivery_note_number or "N/A"))
                
                # Current GRV
                grv_item = QTableWidgetItem(coupon.grv_reference or "Not Set")
                if coupon.grv_reference:
                    grv_item.setBackground(QColor("#d4edda"))
                    grv_item.setForeground(QColor("#155724"))
                else:
                    grv_item.setBackground(QColor("#fff3cd"))
                    grv_item.setForeground(QColor("#856404"))
                self.results_table.setItem(row, 6, grv_item)
            
            # Show summary
            coupons_with_grv = sum(1 for c in self.found_coupons if c.grv_reference)
            self.summary_label.setText(
                f"📊 Bundle Summary: {len(self.found_coupons)} coupon(s) | "
                f"Total Quantity: {total_quantity} pieces | "
                f"Delivery Note: {delivery_note} | "
                f"With GRV: {coupons_with_grv} | "
                f"Without GRV: {len(self.found_coupons) - coupons_with_grv}"
            )
            self.summary_label.show()
            
            # Enable save button
            self.save_btn.setEnabled(True)
            
            QMessageBox.information(
                self,
                "Bundle Found",
                f"✅ Found {len(self.found_coupons)} verified coupon(s) in this bundle\n\n"
                f"Verification Code: {search_term}\n"
                f"Delivery Note: {delivery_note}\n"
                f"Total Quantity: {total_quantity} pieces\n\n"
                f"You can now enter a GRV reference for this bundle."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Search Error",
                f"Failed to search for coupons:\n{str(e)}"
            )
    
    def save_grv_reference(self):
        """Save GRV reference to all found coupons."""
        if not self.found_coupons:
            QMessageBox.warning(
                self,
                "No Coupons",
                "Please search for coupons first."
            )
            return
        
        grv_ref = self.grv_input.text().strip()
        if not grv_ref:
            QMessageBox.warning(
                self,
                "Missing GRV Reference",
                "Please enter a GRV reference number."
            )
            self.grv_input.setFocus()
            return
        
        # Check if any coupons already have a GRV
        existing_grv = [c for c in self.found_coupons if c.grv_reference]
        if existing_grv:
            reply = QMessageBox.question(
                self,
                "Overwrite Existing GRV?",
                f"⚠️ {len(existing_grv)} coupon(s) already have a GRV reference.\n\n"
                f"Do you want to overwrite them with the new GRV reference: {grv_ref}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Confirmation
        total_qty = sum(c.quantity_pieces for c in self.found_coupons)
        ver_ref = self.found_coupons[0].verification_reference if self.found_coupons[0].verification_reference else "N/A"
        dn_ref = self.found_coupons[0].delivery_note_number if self.found_coupons[0].delivery_note_number else "N/A"
        
        reply = QMessageBox.question(
            self,
            "Confirm GRV Assignment",
            f"Are you sure you want to assign GRV reference to this bundle?\n\n"
            f"GRV Reference: {grv_ref}\n"
            f"Verification Code: {ver_ref}\n"
            f"Delivery Note: {dn_ref}\n"
            f"Coupons: {len(self.found_coupons)}\n"
            f"Total Quantity: {total_qty} pieces\n\n"
            f"This will update all {len(self.found_coupons)} coupon(s).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        try:
            # Convert to uppercase for consistency
            grv_ref = grv_ref.upper()
            
            # Update all coupons
            updated_count = 0
            for coupon in self.found_coupons:
                coupon.grv_reference = grv_ref
                self.db_manager.update(coupon)
                updated_count += 1
            
            QMessageBox.information(
                self,
                "GRV Reference Saved",
                f"✅ Successfully assigned GRV reference to {updated_count} coupon(s)!\n\n"
                f"GRV Reference: {grv_ref}\n"
                f"Coupons Updated: {updated_count}\n"
                f"Total Quantity: {total_qty} pieces"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save GRV reference:\n{str(e)}"
            )
