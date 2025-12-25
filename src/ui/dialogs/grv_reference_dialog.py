"""
GRV Reference Dialog - Add GRV (Goods Received Voucher) references to verified bundles.

Allows users to search for verified bundles by verification number or delivery note number,
then assign a GRV reference to all coupons in the selected bundle.
"""

from datetime import datetime
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from sqlalchemy import text, func
from sqlalchemy.orm import joinedload

from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon, MedicalCentre
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class AddGRVReferenceDialog(QDialog):
    """Dialog for adding GRV reference to delivery note bundles."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.bundles_data = []  # List of bundle dictionaries
        self.selected_bundle = None  # Will store list of coupons in selected bundle
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Add GRV Reference")
        self.setModal(True)
        self.resize(1100, 750)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🔍 Search Delivery Note Bundles")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Search by Verification Number or Delivery Note Number (partial match supported).\n"
            "Select a bundle from the results to add a GRV reference."
        )
        instructions.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Search section
        search_layout = QHBoxLayout()
        
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter verification number or delivery note number...")
        self.search_input.setStyleSheet("padding: 8px; font-size: 13px; border: 2px solid #3498db; border-radius: 4px;")
        self.search_input.returnPressed.connect(self.search_bundles)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self.search_bundles)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Results table
        results_label = QLabel("📦 Found Bundles:")
        results_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Verification Ref", "DN Number", "Health Centre", 
            "Total Coupons", "Total Pieces", "Current GRV", "DN Date"
        ])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Verification
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # DN Number
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Health Centre
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Coupons
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Pieces
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # GRV
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # DN Date
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.results_table.itemSelectionChanged.connect(self.on_bundle_selected)
        layout.addWidget(self.results_table)
        
        # Bundle details
        details_label = QLabel("📋 Bundle Details:")
        details_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.details_text)
        
        # GRV Reference input
        grv_layout = QHBoxLayout()
        
        grv_label = QLabel("📄 GRV Reference:")
        grv_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        grv_layout.addWidget(grv_label)
        
        self.grv_input = QLineEdit()
        self.grv_input.setPlaceholderText("Enter GRV reference number...")
        self.grv_input.setStyleSheet("padding: 8px; font-size: 13px; border: 2px solid #27ae60; border-radius: 4px;")
        grv_layout.addWidget(self.grv_input)
        
        layout.addLayout(grv_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #95a5a6;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("💾 Save GRV Reference")
        self.save_btn.clicked.connect(self.save_grv_reference)
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumWidth(180)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def search_bundles(self):
        """Search for bundles by verification reference or delivery note number."""
        search_term = self.search_input.text().strip()
        
        if not search_term:
            QMessageBox.warning(
                self,
                "Empty Search",
                "Please enter a verification number or delivery note number to search."
            )
            return
        
        try:
            # Query bundles using partial match on both fields
            with self.db_manager.get_session() as session:
                # Get all verified coupons that match the search term
                coupons = session.query(PatientCoupon).options(
                    joinedload(PatientCoupon.product),
                    joinedload(PatientCoupon.medical_centre),
                    joinedload(PatientCoupon.distribution_location)
                ).filter(
                    PatientCoupon.verified == True,
                    (
                        (PatientCoupon.verification_reference.ilike(f'%{search_term}%')) |
                        (PatientCoupon.delivery_note_number.ilike(f'%{search_term}%'))
                    )
                ).all()
                
                if not coupons:
                    QMessageBox.information(
                        self,
                        "No Results",
                        f"No verified bundles found matching: {search_term}\n\n"
                        f"Please check:\n"
                        f"• The verification number or DN number is correct\n"
                        f"• The coupons have been verified (confirmed delivered)\n"
                        f"• The search term matches part of the verification/DN number"
                    )
                    self.results_table.setRowCount(0)
                    self.details_text.clear()
                    self.save_btn.setEnabled(False)
                    return
                
                # Group coupons by verification_reference + delivery_note_number combination
                bundles_dict = {}
                for coupon in coupons:
                    # Use both verification ref and DN as key for uniqueness
                    key = (coupon.verification_reference or "N/A", coupon.delivery_note_number or "N/A")
                    if key not in bundles_dict:
                        bundles_dict[key] = []
                    bundles_dict[key].append(coupon)
                
                # Convert to list of bundle data
                self.bundles_data = []
                for (ver_ref, dn_num), coupons_list in bundles_dict.items():
                    # Get health centre name from first coupon
                    health_centre = "Unknown"
                    if coupons_list[0].medical_centre:
                        health_centre = coupons_list[0].medical_centre.name
                    
                    # Get DN date from first coupon (if available)
                    dn_date = "N/A"
                    if coupons_list[0].date_verified:
                        dn_date = coupons_list[0].date_verified.strftime("%Y-%m-%d")
                    
                    # Calculate totals
                    total_pieces = sum(c.quantity_pieces for c in coupons_list)
                    
                    # Get GRV reference (should be same for all in bundle)
                    grv_ref = coupons_list[0].grv_reference or "Not Set"
                    
                    self.bundles_data.append({
                        'verification_ref': ver_ref,
                        'dn_number': dn_num,
                        'health_centre': health_centre,
                        'coupon_count': len(coupons_list),
                        'total_pieces': total_pieces,
                        'grv_ref': grv_ref,
                        'dn_date': dn_date,
                        'coupons': coupons_list
                    })
                
                # Sort bundles by verification ref
                self.bundles_data.sort(key=lambda x: x['verification_ref'])
                
                # Populate results table
                self.results_table.setRowCount(len(self.bundles_data))
                
                for row, bundle in enumerate(self.bundles_data):
                    # Verification Reference
                    self.results_table.setItem(row, 0, QTableWidgetItem(bundle['verification_ref']))
                    
                    # DN Number
                    self.results_table.setItem(row, 1, QTableWidgetItem(bundle['dn_number']))
                    
                    # Health Centre
                    self.results_table.setItem(row, 2, QTableWidgetItem(bundle['health_centre']))
                    
                    # Total Coupons
                    count_item = QTableWidgetItem(str(bundle['coupon_count']))
                    count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.results_table.setItem(row, 3, count_item)
                    
                    # Total Pieces
                    pieces_item = QTableWidgetItem(str(bundle['total_pieces']))
                    pieces_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.results_table.setItem(row, 4, pieces_item)
                    
                    # Current GRV
                    grv_item = QTableWidgetItem(bundle['grv_ref'])
                    if bundle['grv_ref'] != "Not Set":
                        grv_item.setBackground(QColor("#d4edda"))
                        grv_item.setForeground(QColor("#155724"))
                    else:
                        grv_item.setBackground(QColor("#fff3cd"))
                        grv_item.setForeground(QColor("#856404"))
                    self.results_table.setItem(row, 5, grv_item)
                    
                    # DN Date
                    self.results_table.setItem(row, 6, QTableWidgetItem(bundle['dn_date']))
                
                QMessageBox.information(
                    self,
                    "Search Complete",
                    f"✅ Found {len(self.bundles_data)} bundle(s) matching: {search_term}\n\n"
                    f"Select a bundle from the table to view details and add GRV reference."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Search Error",
                f"Failed to search for bundles:\n{str(e)}"
            )
    
    def on_bundle_selected(self):
        """Handle bundle selection from table."""
        selected_row = self.results_table.currentRow()
        
        if selected_row < 0 or selected_row >= len(self.bundles_data):
            self.selected_bundle = None
            self.details_text.clear()
            self.save_btn.setEnabled(False)
            return
        
        # Get selected bundle data
        bundle = self.bundles_data[selected_row]
        self.selected_bundle = bundle['coupons']
        
        # Populate GRV input with current value if exists
        if bundle['grv_ref'] != "Not Set":
            self.grv_input.setText(bundle['grv_ref'])
        else:
            self.grv_input.clear()
        
        # Build details text
        details = []
        details.append(f"═══════════════════════════════════════════════════")
        details.append(f"BUNDLE DETAILS")
        details.append(f"═══════════════════════════════════════════════════")
        details.append(f"")
        details.append(f"Verification Reference: {bundle['verification_ref']}")
        details.append(f"Delivery Note Number:   {bundle['dn_number']}")
        details.append(f"Health Centre:          {bundle['health_centre']}")
        details.append(f"DN Date:                {bundle['dn_date']}")
        details.append(f"")
        details.append(f"Total Coupons:          {bundle['coupon_count']}")
        details.append(f"Total Pieces:           {bundle['total_pieces']}")
        details.append(f"Current GRV:            {bundle['grv_ref']}")
        details.append(f"")
        details.append(f"───────────────────────────────────────────────────")
        details.append(f"COUPONS IN THIS BUNDLE:")
        details.append(f"───────────────────────────────────────────────────")
        
        for i, coupon in enumerate(bundle['coupons'], 1):
            patient = coupon.patient_name or "N/A"
            product = coupon.product.name if coupon.product else "Unknown"
            qty = coupon.quantity_pieces
            details.append(f"{i}. {patient} - {product} ({qty} pcs)")
        
        self.details_text.setText("\n".join(details))
        
        # Enable save button
        self.save_btn.setEnabled(True)
    
    def save_grv_reference(self):
        """Save GRV reference to all coupons in selected bundle."""
        if not self.selected_bundle:
            QMessageBox.warning(
                self,
                "No Bundle Selected",
                "Please select a bundle from the search results first."
            )
            return
        
        grv_ref = self.grv_input.text().strip()
        
        if not grv_ref:
            QMessageBox.warning(
                self,
                "Empty GRV Reference",
                "Please enter a GRV reference number."
            )
            return
        
        try:
            # Update all coupons in the bundle
            with self.db_manager.get_session() as session:
                updated_count = 0
                
                for coupon in self.selected_bundle:
                    # Get coupon from session
                    db_coupon = session.query(PatientCoupon).get(coupon.id)
                    if db_coupon:
                        db_coupon.grv_reference = grv_ref
                        updated_count += 1
                
                # Commit happens automatically on context manager exit
            
            QMessageBox.information(
                self,
                "Success",
                f"✅ GRV reference '{grv_ref}' has been successfully added to {updated_count} coupon(s) in the bundle.\n\n"
                f"Verification Reference: {self.selected_bundle[0].verification_reference}\n"
                f"Delivery Note: {self.selected_bundle[0].delivery_note_number}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save GRV reference:\n{str(e)}"
            )


# Alias for backwards compatibility
GRVReferenceDialog = AddGRVReferenceDialog
