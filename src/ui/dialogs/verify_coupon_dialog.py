"""
Verify Coupon Dialog - Verification workflow for patient coupons.

Handles the verification process including stock deduction and reference generation.
"""

from datetime import datetime
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
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon
from src.services.stock_service import StockService


class VerifyCouponDialog(QDialog):
    """Dialog for verifying a patient coupon and deducting stock."""
    
    def __init__(self, db_manager: DatabaseManager, coupon: PatientCoupon, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.coupon = coupon
        self.stock_service = StockService(db_manager)
        
        self.init_ui()
        self.check_stock_availability()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Verify Coupon")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("✅ Verify Patient Coupon")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Warning message
        warning = QLabel(
            "⚠️ This action will deduct stock from purchase orders using FIFO method.\n"
            "This cannot be undone except by deleting the coupon."
        )
        warning.setStyleSheet(
            "background-color: #fff3cd; padding: 10px; border-radius: 4px; "
            "color: #856404; border-left: 4px solid #ffc107;"
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        layout.addSpacing(10)
        
        # Coupon details section
        details_label = QLabel("📋 Coupon Details")
        details_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(details_label)
        
        # Form with coupon info
        form_layout = QFormLayout()
        
        # Patient Name
        patient_name_display = QLineEdit(self.coupon.patient_name)
        patient_name_display.setReadOnly(True)
        patient_name_display.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("Patient Name:", patient_name_display)
        
        # CPR
        cpr_display = QLineEdit(self.coupon.cpr)
        cpr_display.setReadOnly(True)
        cpr_display.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("CPR:", cpr_display)
        
        # Product
        product_name = self.coupon.product.name if self.coupon.product else "Unknown"
        product_display = QLineEdit(product_name)
        product_display.setReadOnly(True)
        product_display.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("Product:", product_display)
        
        # Quantity
        quantity_display = QLineEdit(f"{self.coupon.quantity_pieces} pieces")
        quantity_display.setReadOnly(True)
        quantity_display.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("Quantity:", quantity_display)
        
        # Medical Centre
        centre_name = self.coupon.medical_centre.name if self.coupon.medical_centre else "Unknown"
        centre_display = QLineEdit(centre_name)
        centre_display.setReadOnly(True)
        centre_display.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("Medical Centre:", centre_display)
        
        # Distribution Location
        location_name = self.coupon.distribution_location.name if self.coupon.distribution_location else "Unknown"
        location_display = QLineEdit(location_name)
        location_display.setReadOnly(True)
        location_display.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("Distribution:", location_display)
        
        layout.addLayout(form_layout)
        
        layout.addSpacing(15)
        
        # Stock availability section
        stock_label = QLabel("📦 Stock Availability")
        stock_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(stock_label)
        
        self.stock_status_label = QLabel()
        self.stock_status_label.setWordWrap(True)
        layout.addWidget(self.stock_status_label)
        
        self.stock_details_text = QTextEdit()
        self.stock_details_text.setReadOnly(True)
        self.stock_details_text.setMaximumHeight(100)
        self.stock_details_text.setStyleSheet("background-color: #f5f5f5; font-family: monospace;")
        layout.addWidget(self.stock_details_text)
        
        layout.addSpacing(15)
        
        # Verification reference section
        ver_label = QLabel("🔑 Verification Reference")
        ver_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(ver_label)
        
        ver_note = QLabel("A unique verification reference will be generated automatically.")
        ver_note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(ver_note)
        
        self.verification_ref_display = QLineEdit()
        self.verification_ref_display.setReadOnly(True)
        self.verification_ref_display.setStyleSheet(
            "background-color: #e3f2fd; font-weight: bold; font-size: 14px; "
            "padding: 8px; border: 2px solid #2196f3;"
        )
        self.verification_ref_display.setPlaceholderText("Will be generated upon verification...")
        layout.addWidget(self.verification_ref_display)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        self.verify_btn = QPushButton("✅ Verify & Deduct Stock")
        self.verify_btn.clicked.connect(self.verify_coupon)
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
    
    def check_stock_availability(self):
        """Check if enough stock is available for verification."""
        try:
            # Validate stock availability
            is_available, message = self.stock_service.validate_stock_availability(
                self.coupon.product_id,
                self.coupon.quantity_pieces
            )
            
            if is_available:
                self.stock_status_label.setText(
                    f"✅ {message}"
                )
                self.stock_status_label.setStyleSheet(
                    "background-color: #d4edda; padding: 10px; border-radius: 4px; "
                    "color: #155724; font-weight: bold;"
                )
                self.verify_btn.setEnabled(True)
                
                # Show stock details
                total_stock = self.stock_service.get_total_stock_by_product(self.coupon.product_id)
                remaining_after = total_stock - self.coupon.quantity_pieces
                
                details = (
                    f"Current Stock: {total_stock} pieces\n"
                    f"Required: {self.coupon.quantity_pieces} pieces\n"
                    f"Remaining After: {remaining_after} pieces"
                )
                self.stock_details_text.setText(details)
                
                # Generate preview of verification reference
                preview_ref = self.generate_verification_reference()
                self.verification_ref_display.setText(preview_ref)
                
            else:
                self.stock_status_label.setText(
                    f"❌ {message}"
                )
                self.stock_status_label.setStyleSheet(
                    "background-color: #f8d7da; padding: 10px; border-radius: 4px; "
                    "color: #721c24; font-weight: bold;"
                )
                self.verify_btn.setEnabled(False)
                
                # Show what's available
                total_stock = self.stock_service.get_total_stock_by_product(self.coupon.product_id)
                shortage = self.coupon.quantity_pieces - total_stock
                
                details = (
                    f"Current Stock: {total_stock} pieces\n"
                    f"Required: {self.coupon.quantity_pieces} pieces\n"
                    f"Shortage: {shortage} pieces\n\n"
                    f"Please add more purchase orders for this product."
                )
                self.stock_details_text.setText(details)
                
        except Exception as e:
            self.stock_status_label.setText(
                f"❌ Error checking stock: {str(e)}"
            )
            self.stock_status_label.setStyleSheet(
                "background-color: #f8d7da; padding: 10px; border-radius: 4px; "
                "color: #721c24;"
            )
            self.verify_btn.setEnabled(False)
    
    def generate_verification_reference(self) -> str:
        """
        Generate a unique verification reference.
        
        Format: VER-YYYYMMDD-HHMMSS-COUPONID
        Example: VER-20241108-143025-00123
        """
        now = datetime.now()
        return f"VER-{now.strftime('%Y%m%d-%H%M%S')}-{self.coupon.id:05d}"
    
    def verify_coupon(self):
        """Verify the coupon and deduct stock."""
        # Final confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Verification",
            f"Are you sure you want to verify this coupon?\n\n"
            f"Patient: {self.coupon.patient_name}\n"
            f"CPR: {self.coupon.cpr}\n"
            f"Product: {self.coupon.product.name if self.coupon.product else 'Unknown'}\n"
            f"Quantity: {self.coupon.quantity_pieces} pieces\n\n"
            f"Stock will be deducted using FIFO method.\n"
            f"This action cannot be undone except by deleting the coupon.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        try:
            # Generate verification reference
            verification_ref = self.generate_verification_reference()
            
            # Deduct stock using FIFO
            self.stock_service.deduct_stock(
                self.coupon.product_id,
                self.coupon.quantity_pieces,
                self.coupon.id
            )
            
            # Update coupon
            self.coupon.verified = True
            self.coupon.verification_reference = verification_ref
            self.coupon.verified_at = datetime.now()
            
            self.db_manager.update(self.coupon)
            
            # Success message
            QMessageBox.information(
                self,
                "Verification Successful",
                f"✅ Coupon verified successfully!\n\n"
                f"Verification Reference: {verification_ref}\n"
                f"Stock deducted: {self.coupon.quantity_pieces} pieces\n"
                f"Patient: {self.coupon.patient_name}\n"
                f"CPR: {self.coupon.cpr}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Verification Error",
                f"Failed to verify coupon:\n{str(e)}\n\n"
                f"No changes have been made to the database."
            )
