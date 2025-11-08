"""
Coupon Dialog - Add/Edit dialog for patient coupon management.

Provides a form for creating new coupons or editing pending ones.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon, Product, MedicalCentre, DistributionLocation
from src.utils import validate_cpr, validate_name, validate_quantity, sanitize_input


class CouponDialog(QDialog):
    """Dialog for adding or editing a patient coupon."""
    
    def __init__(self, db_manager: DatabaseManager, coupon: Optional[PatientCoupon] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.coupon = coupon
        self.is_edit_mode = coupon is not None
        self.products = []
        self.medical_centres = []
        self.distribution_locations = []
        
        self.init_ui()
        self.load_dropdown_data()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Edit Coupon" if self.is_edit_mode else "Add New Coupon")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("✏️ Edit Coupon" if self.is_edit_mode else "➕ Add New Coupon")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        # Coupon Reference (user-entered)
        self.coupon_ref_input = QLineEdit()
        self.coupon_ref_input.setPlaceholderText("Enter coupon reference (e.g., CPN-001)")
        form_layout.addRow("Coupon Ref: *", self.coupon_ref_input)
        
        # Patient Name
        self.patient_name_input = QLineEdit()
        self.patient_name_input.setPlaceholderText("Enter patient full name")
        form_layout.addRow("Patient Name: *", self.patient_name_input)
        
        # CPR (Civil Personal Record)
        self.cpr_input = QLineEdit()
        self.cpr_input.setPlaceholderText("Enter CPR number (e.g., 123456789)")
        self.cpr_input.setMaxLength(15)
        form_layout.addRow("CPR: *", self.cpr_input)
        
        # Product Selection
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        form_layout.addRow("Product: *", self.product_combo)
        
        # Product Reference Display
        self.product_ref_display = QLineEdit()
        self.product_ref_display.setReadOnly(True)
        self.product_ref_display.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("Product Ref:", self.product_ref_display)
        
        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(1)
        self.quantity_input.setSuffix(" pieces")
        form_layout.addRow("Quantity: *", self.quantity_input)
        
        # Medical Centre
        self.medical_centre_combo = QComboBox()
        form_layout.addRow("Medical Centre: *", self.medical_centre_combo)
        
        # Distribution Location
        self.distribution_location_combo = QComboBox()
        form_layout.addRow("Distribution: *", self.distribution_location_combo)
        
        layout.addLayout(form_layout)
        
        # Stock availability info
        self.stock_info_label = QLabel()
        self.stock_info_label.setStyleSheet(
            "background-color: #e8f5e9; padding: 10px; border-radius: 4px; "
            "color: #2e7d32; font-weight: bold;"
        )
        self.stock_info_label.hide()
        layout.addWidget(self.stock_info_label)
        
        # Required fields note
        note = QLabel("* Required fields")
        note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(note)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("Update" if self.is_edit_mode else "Add Coupon")
        self.save_btn.clicked.connect(self.save_coupon)
        self.save_btn.setMinimumWidth(100)
        self.save_btn.setStyleSheet("""
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
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def load_dropdown_data(self):
        """Load data for all dropdowns."""
        try:
            # Load products
            self.products = self.db_manager.get_all(Product)
            self.product_combo.clear()
            self.product_combo.addItem("-- Select Product --", None)
            for product in self.products:
                self.product_combo.addItem(f"{product.name}", product.id)
            
            # Load medical centres
            self.medical_centres = self.db_manager.get_all(MedicalCentre)
            self.medical_centre_combo.clear()
            self.medical_centre_combo.addItem("-- Select Medical Centre --", None)
            for centre in self.medical_centres:
                self.medical_centre_combo.addItem(centre.name, centre.id)
            
            # Load distribution locations
            self.distribution_locations = self.db_manager.get_all(DistributionLocation)
            self.distribution_location_combo.clear()
            self.distribution_location_combo.addItem("-- Select Distribution Location --", None)
            for location in self.distribution_locations:
                self.distribution_location_combo.addItem(location.name, location.id)
            
            if not self.products:
                QMessageBox.warning(
                    self,
                    "No Products",
                    "No products found.\nPlease add products first."
                )
            
            if not self.medical_centres:
                QMessageBox.warning(
                    self,
                    "No Medical Centres",
                    "No medical centres found.\nPlease add medical centres first."
                )
            
            if not self.distribution_locations:
                QMessageBox.warning(
                    self,
                    "No Distribution Locations",
                    "No distribution locations found.\nPlease add distribution locations first."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Data",
                f"Failed to load dropdown data:\n{str(e)}"
            )
    
    def on_product_changed(self, index):
        """Handle product selection change and show stock info."""
        product_id = self.product_combo.currentData()
        
        if product_id:
            # Find the product
            product = next((p for p in self.products if p.id == product_id), None)
            if product:
                self.product_ref_display.setText(product.reference)
                
                # Check available stock
                try:
                    from services.stock_service import StockService
                    stock_service = StockService(self.db_manager)
                    total_stock = stock_service.get_total_stock_by_product(product_id)
                    
                    if total_stock > 0:
                        self.stock_info_label.setText(
                            f"✅ Available Stock: {total_stock} pieces"
                        )
                        self.stock_info_label.setStyleSheet(
                            "background-color: #e8f5e9; padding: 10px; border-radius: 4px; "
                            "color: #2e7d32; font-weight: bold;"
                        )
                    else:
                        self.stock_info_label.setText(
                            f"⚠️ No Stock Available - Coupon can be created but not verified"
                        )
                        self.stock_info_label.setStyleSheet(
                            "background-color: #fff3cd; padding: 10px; border-radius: 4px; "
                            "color: #856404; font-weight: bold;"
                        )
                    
                    self.stock_info_label.show()
                    
                except Exception as e:
                    self.stock_info_label.hide()
        else:
            self.product_ref_display.clear()
            self.stock_info_label.hide()
    
    def populate_fields(self):
        """Populate form fields with existing coupon data."""
        if self.coupon:
            self.coupon_ref_input.setText(self.coupon.coupon_reference)
            self.patient_name_input.setText(self.coupon.patient_name)
            self.cpr_input.setText(self.coupon.cpr)
            
            # Select product
            for i in range(self.product_combo.count()):
                if self.product_combo.itemData(i) == self.coupon.product_id:
                    self.product_combo.setCurrentIndex(i)
                    break
            
            self.quantity_input.setValue(self.coupon.quantity_pieces)
            
            # Select medical centre
            for i in range(self.medical_centre_combo.count()):
                if self.medical_centre_combo.itemData(i) == self.coupon.medical_centre_id:
                    self.medical_centre_combo.setCurrentIndex(i)
                    break
            
            # Select distribution location
            for i in range(self.distribution_location_combo.count()):
                if self.distribution_location_combo.itemData(i) == self.coupon.distribution_location_id:
                    self.distribution_location_combo.setCurrentIndex(i)
                    break
    
    def validate_input(self) -> tuple[bool, str]:
        """
        Validate user input using centralized validators.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Sanitize inputs
        patient_name = sanitize_input(self.patient_name_input.text())
        cpr = sanitize_input(self.cpr_input.text())
        product_id = self.product_combo.currentData()
        medical_centre_id = self.medical_centre_combo.currentData()
        distribution_location_id = self.distribution_location_combo.currentData()
        quantity = self.quantity_input.value()
        
        # Validate patient name
        is_valid, error_msg = validate_name(patient_name, field_name="Patient name")
        if not is_valid:
            return False, error_msg
        
        # Validate CPR
        is_valid, error_msg = validate_cpr(cpr)
        if not is_valid:
            return False, f"CPR error: {error_msg}"
        
        # Validate product selection
        if not product_id:
            return False, "Please select a product."
        
        # Validate medical centre selection
        if not medical_centre_id:
            return False, "Please select a medical centre."
        
        # Validate distribution location selection
        if not distribution_location_id:
            return False, "Please select a distribution location."
        
        # Validate quantity
        is_valid, error_msg = validate_quantity(quantity)
        if not is_valid:
            return False, f"Quantity error: {error_msg}"
        
        return True, ""
    
    def save_coupon(self):
        """Save the coupon to database."""
        # Validate input
        is_valid, error_msg = self.validate_input()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        try:
            # Sanitize inputs
            coupon_reference = sanitize_input(self.coupon_ref_input.text()).upper()
            patient_name = sanitize_input(self.patient_name_input.text())
            cpr = sanitize_input(self.cpr_input.text())
            product_id = self.product_combo.currentData()
            quantity = self.quantity_input.value()
            medical_centre_id = self.medical_centre_combo.currentData()
            distribution_location_id = self.distribution_location_combo.currentData()
            
            # Validate coupon reference is not empty
            if not coupon_reference:
                QMessageBox.warning(self, "Validation Error", "Coupon reference cannot be empty.")
                return
            
            if self.is_edit_mode:
                # Update existing coupon
                self.coupon.coupon_reference = coupon_reference
                self.coupon.patient_name = patient_name
                self.coupon.cpr = cpr
                self.coupon.product_id = product_id
                self.coupon.quantity_pieces = quantity
                self.coupon.medical_centre_id = medical_centre_id
                self.coupon.distribution_location_id = distribution_location_id
                
                self.db_manager.update(self.coupon)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Coupon {coupon_reference} for {patient_name} updated successfully!"
                )
            else:
                # Create new coupon
                new_coupon = PatientCoupon(
                    coupon_reference=coupon_reference,
                    patient_name=patient_name,
                    cpr=cpr,
                    product_id=product_id,
                    quantity_pieces=quantity,
                    medical_centre_id=medical_centre_id,
                    distribution_location_id=distribution_location_id,
                    verified=False  # Initially not verified
                )
                self.db_manager.add(new_coupon)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Coupon for {patient_name} added successfully!\n"
                    f"Quantity: {quantity} pieces\n"
                    f"Status: Pending verification"
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Coupon",
                f"Failed to save coupon:\n{str(e)}"
            )
