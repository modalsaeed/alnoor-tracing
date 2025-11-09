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
from src.services.stock_service import StockService


class VerifyCouponDialog(QDialog):
    """Dialog for verifying patient coupons with manual verification reference entry."""
    
    def __init__(self, db_manager: DatabaseManager, coupons: List[PatientCoupon], parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.coupons = coupons if isinstance(coupons, list) else [coupons]
        self.stock_service = StockService(db_manager)
        
        self.init_ui()
        self.load_coupon_details()
        self.check_stock_availability()
    
    def init_ui(self):
        """Initialize the user interface."""
        coupon_count = len(self.coupons)
        self.setWindowTitle(f"Verify {'Coupons' if coupon_count > 1 else 'Coupon'}")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(f"✅ Verify {coupon_count} {'Coupons' if coupon_count > 1 else 'Coupon'}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Info message
        info = QLabel(
            "The medical centre/ministry will provide a verification reference after confirming the data is correct.\n"
            "Enter that reference below to mark these coupons as verified and deduct stock."
        )
        info.setStyleSheet(
            "background-color: #e3f2fd; padding: 10px; border-radius: 4px; "
            "color: #0c5460; border-left: 4px solid #2196f3;"
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
        
        # Stock availability section
        stock_label = QLabel("📦 Stock Availability")
        stock_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(stock_label)
        
        self.stock_status_label = QLabel()
        self.stock_status_label.setWordWrap(True)
        layout.addWidget(self.stock_status_label)
        
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
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        self.verify_btn = QPushButton("✅ Verify & Deduct Stock")
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
            QPushButton:disabled {
                background-color: #95a5a6;
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
            self.coupons_table.setItem(row, 1, QTableWidgetItem(coupon.patient_name))
            
            # CPR
            self.coupons_table.setItem(row, 2, QTableWidgetItem(coupon.cpr))
            
            # Product
            product_name = coupon.product.name if coupon.product else "Unknown"
            self.coupons_table.setItem(row, 3, QTableWidgetItem(product_name))
            
            # Quantity
            qty_item = QTableWidgetItem(f"{coupon.quantity_pieces} pieces")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.coupons_table.setItem(row, 4, qty_item)
    
    def check_stock_availability(self):
        """Check if enough stock is available for all coupons."""
        try:
            # Group coupons by product and calculate total quantity needed
            product_requirements = {}
            for coupon in self.coupons:
                product_id = coupon.product_id
                if product_id not in product_requirements:
                    product_requirements[product_id] = {
                        'product_name': coupon.product.name if coupon.product else "Unknown",
                        'total_needed': 0,
                        'current_stock': 0,
                        'coupon_count': 0
                    }
                product_requirements[product_id]['total_needed'] += coupon.quantity_pieces
                product_requirements[product_id]['coupon_count'] += 1
            
            # Check stock availability for each product
            all_available = True
            status_messages = []
            
            for product_id, req in product_requirements.items():
                current_stock = self.stock_service.get_total_stock_by_product(product_id)
                req['current_stock'] = current_stock
                
                is_available, message = self.stock_service.validate_stock_availability(
                    product_id,
                    req['total_needed']
                )
                
                if is_available:
                    remaining = current_stock - req['total_needed']
                    status_messages.append(
                        f"✅ {req['product_name']}: {req['total_needed']} pieces available "
                        f"(Current: {current_stock}, After: {remaining})"
                    )
                else:
                    shortage = req['total_needed'] - current_stock
                    status_messages.append(
                        f"❌ {req['product_name']}: Insufficient stock "
                        f"(Need: {req['total_needed']}, Available: {current_stock}, Short: {shortage})"
                    )
                    all_available = False
            
            # Update UI based on availability
            status_text = "\n".join(status_messages)
            
            if all_available:
                self.stock_status_label.setText(
                    f"✅ All required stock is available for {len(self.coupons)} coupon(s)"
                )
                self.stock_status_label.setStyleSheet(
                    "background-color: #d4edda; padding: 10px; border-radius: 4px; "
                    "color: #155724; font-weight: bold;"
                )
                self.verify_btn.setEnabled(True)
            else:
                self.stock_status_label.setText(
                    f"❌ Insufficient stock for some products"
                )
                self.stock_status_label.setStyleSheet(
                    "background-color: #f8d7da; padding: 10px; border-radius: 4px; "
                    "color: #721c24; font-weight: bold;"
                )
                self.verify_btn.setEnabled(False)
                
        except Exception as e:
            self.stock_status_label.setText(
                f"❌ Error checking stock: {str(e)}"
            )
            self.stock_status_label.setStyleSheet(
                "background-color: #f8d7da; padding: 10px; border-radius: 4px; "
                "color: #721c24;"
            )
            self.verify_btn.setEnabled(False)
    
    def verify_coupons(self):
        """Verify all coupons and deduct stock."""
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
        
        # Build confirmation message
        coupon_list = "\n".join([
            f"  • {c.patient_name} ({c.cpr}) - {c.product.name if c.product else 'Unknown'} - {c.quantity_pieces} pieces"
            for c in self.coupons
        ])
        
        total_quantity = sum(c.quantity_pieces for c in self.coupons)
        
        reply = QMessageBox.question(
            self,
            "Confirm Batch Verification",
            f"Are you sure you want to verify {len(self.coupons)} coupon(s)?\n\n"
            f"Verification Reference: {verification_ref}\n\n"
            f"Coupons:\n{coupon_list}\n\n"
            f"Total Quantity: {total_quantity} pieces\n\n"
            f"Stock will be deducted using FIFO method.\n"
            f"This action cannot be undone except by deleting the coupons.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        try:
            # Convert to uppercase for consistency
            verification_ref = verification_ref.upper()
            
            # Process each coupon
            verified_count = 0
            failed_coupons = []
            
            for coupon in self.coupons:
                try:
                    # Deduct stock using FIFO
                    self.stock_service.deduct_stock(
                        coupon.product_id,
                        coupon.quantity_pieces,
                        coupon.id
                    )
                    
                    # Update coupon
                    coupon.verified = True
                    coupon.verification_reference = verification_ref
                    coupon.verified_at = datetime.now()
                    
                    self.db_manager.update(coupon)
                    verified_count += 1
                    
                except Exception as e:
                    failed_coupons.append(f"{coupon.coupon_reference}: {str(e)}")
            
            # Show results
            if verified_count == len(self.coupons):
                QMessageBox.information(
                    self,
                    "Batch Verification Successful",
                    f"✅ Successfully verified {verified_count} coupon(s)!\n\n"
                    f"Verification Reference: {verification_ref}\n"
                    f"Total Stock Deducted: {total_quantity} pieces\n\n"
                    f"All coupons have been marked as verified."
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
