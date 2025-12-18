"""
Coupon Dialog - Add/Edit dialog for patient coupon management.

Provides a form for creating new coupons or editing pending ones.
"""

from typing import Optional
from datetime import datetime
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
    QCompleter,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate

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
        
        # Patient Name (now optional)
        self.patient_name_input = QLineEdit()
        self.patient_name_input.setPlaceholderText("Enter patient full name (optional)")
        form_layout.addRow("Patient Name:", self.patient_name_input)
        
        # CPR (Civil Personal Record - now optional)
        self.cpr_input = QLineEdit()
        self.cpr_input.setPlaceholderText("Enter CPR number (optional, e.g., 123456789)")
        self.cpr_input.setMaxLength(15)
        form_layout.addRow("CPR:", self.cpr_input)
        
        # Date Received
        self.date_received_input = QDateEdit()
        self.date_received_input.setCalendarPopup(True)
        self.date_received_input.setDate(QDate.currentDate())
        self.date_received_input.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Date Received: *", self.date_received_input)
        
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
        
        # MOH Health Centre with searchable dropdown and quick-add
        medical_centre_layout = QHBoxLayout()
        self.medical_centre_combo = QComboBox()
        self.medical_centre_combo.setEditable(True)
        self.medical_centre_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        medical_centre_layout.addWidget(self.medical_centre_combo, 1)
        
        add_centre_btn = QPushButton("➕")
        add_centre_btn.setMaximumWidth(35)
        add_centre_btn.setToolTip("Quick add new MOH health centre")
        add_centre_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_centre_btn.clicked.connect(self.quick_add_medical_centre)
        medical_centre_layout.addWidget(add_centre_btn)
        
        form_layout.addRow("MOH Health Centre: *", medical_centre_layout)
        
        # Distribution Location with searchable dropdown and quick-add
        distribution_layout = QHBoxLayout()
        self.distribution_location_combo = QComboBox()
        self.distribution_location_combo.setEditable(True)
        self.distribution_location_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        distribution_layout.addWidget(self.distribution_location_combo, 1)
        
        add_location_btn = QPushButton("➕")
        add_location_btn.setMaximumWidth(35)
        add_location_btn.setToolTip("Quick add new distribution location")
        add_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_location_btn.clicked.connect(self.quick_add_distribution_location)
        distribution_layout.addWidget(add_location_btn)
        
        form_layout.addRow("Distribution: *", distribution_layout)
        
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
        note = QLabel("* Required fields | Patient info is optional for bulk entry")
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
            
            # Load medical centres with autocomplete
            self.medical_centres = self.db_manager.get_all(MedicalCentre)
            self.medical_centre_combo.clear()
            self.medical_centre_combo.addItem("-- Select MOH Health Centre --", None)
            centre_names = []
            for centre in self.medical_centres:
                self.medical_centre_combo.addItem(centre.name, centre.id)
                centre_names.append(centre.name)
            
            # Setup autocomplete for medical centres
            if centre_names:
                centre_completer = QCompleter(centre_names, self)
                centre_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                centre_completer.setFilterMode(Qt.MatchFlag.MatchContains)
                self.medical_centre_combo.setCompleter(centre_completer)
            
            # Load distribution locations with autocomplete
            self.distribution_locations = self.db_manager.get_all(DistributionLocation)
            self.distribution_location_combo.clear()
            self.distribution_location_combo.addItem("-- Select Distribution Location --", None)
            location_names = []
            for location in self.distribution_locations:
                self.distribution_location_combo.addItem(location.name, location.id)
                location_names.append(location.name)
            
            # Setup autocomplete for distribution locations
            if location_names:
                location_completer = QCompleter(location_names, self)
                location_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                location_completer.setFilterMode(Qt.MatchFlag.MatchContains)
                self.distribution_location_combo.setCompleter(location_completer)
            
            if not self.products:
                QMessageBox.warning(
                    self,
                    "No Products",
                    "No products found.\nPlease add products first."
                )
            
            if not self.medical_centres:
                QMessageBox.warning(
                    self,
                    "No MOH Health Centres",
                    "No MOH health centres found.\nPlease add MOH health centres first."
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
            
            # Handle optional patient fields
            if self.coupon.patient_name:
                self.patient_name_input.setText(self.coupon.patient_name)
            
            if self.coupon.cpr:
                self.cpr_input.setText(self.coupon.cpr)
            
            # Set date received
            if self.coupon.date_received:
                qdate = QDate(
                    self.coupon.date_received.year,
                    self.coupon.date_received.month,
                    self.coupon.date_received.day
                )
                self.date_received_input.setDate(qdate)
            
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
        
        # Validate patient name (optional)
        if patient_name:
            is_valid, error_msg = validate_name(patient_name, field_name="Patient name")
            if not is_valid:
                return False, error_msg
        
        # Validate CPR (optional)
        if cpr:
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
            patient_name = sanitize_input(self.patient_name_input.text()) if self.patient_name_input.text().strip() else None
            cpr = sanitize_input(self.cpr_input.text()) if self.cpr_input.text().strip() else None
            product_id = self.product_combo.currentData()
            quantity = self.quantity_input.value()
            medical_centre_id = self.medical_centre_combo.currentData()
            distribution_location_id = self.distribution_location_combo.currentData()
            
            # Get selected date
            selected_date = self.date_received_input.date()
            date_received = datetime(selected_date.year(), selected_date.month(), selected_date.day())
            
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
                self.coupon.date_received = date_received
                
                self.db_manager.update(self.coupon)
                
                patient_info = f"for {patient_name}" if patient_name else ""
                QMessageBox.information(
                    self,
                    "Success",
                    f"Coupon {coupon_reference} {patient_info} updated successfully!"
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
                    verified=False,  # Initially not verified
                    date_received=date_received
                )
                self.db_manager.add(new_coupon)
                
                patient_info = f"for {patient_name}" if patient_name else "(no patient info)"
                QMessageBox.information(
                    self,
                    "Success",
                    f"Coupon {patient_info} added successfully!\n"
                    f"Coupon Ref: {coupon_reference}\n"
                    f"Quantity: {quantity} pieces\n"
                    f"Date: {selected_date.toString('dd/MM/yyyy')}\n"
                    f"Status: Pending verification"
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Coupon",
                f"Failed to save coupon:\n{str(e)}"
            )
    
    def quick_add_medical_centre(self):
        """Quick add a new medical centre with full form."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Medical Centre")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel("➕ Add New Medical Centre")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter medical centre name")
        form_layout.addRow("Name: *", name_input)
        
        reference_input = QLineEdit()
        reference_input.setPlaceholderText("Enter reference code (e.g., MC-001)")
        form_layout.addRow("Reference: *", reference_input)
        
        address_input = QLineEdit()
        address_input.setPlaceholderText("Enter address (optional)")
        form_layout.addRow("Address:", address_input)
        
        contact_input = QLineEdit()
        contact_input.setPlaceholderText("Enter contact person name (optional)")
        form_layout.addRow("Contact Person:", contact_input)
        
        phone_input = QLineEdit()
        phone_input.setPlaceholderText("Enter phone number (optional)")
        form_layout.addRow("Phone:", phone_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet("""
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
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        def save_centre():
            name = sanitize_input(name_input.text().strip())
            reference = sanitize_input(reference_input.text().strip().upper())
            address = sanitize_input(address_input.text().strip()) or None
            contact = sanitize_input(contact_input.text().strip()) or None
            phone = sanitize_input(phone_input.text().strip()) or None
            
            # Validation
            if not name:
                QMessageBox.warning(dialog, "Validation Error", "Name cannot be empty.")
                return
            if not reference:
                QMessageBox.warning(dialog, "Validation Error", "Reference cannot be empty.")
                return
            
            try:
                # Check if already exists
                existing = self.db_manager.get_all(MedicalCentre)
                if any(c.name.lower() == name.lower() for c in existing):
                    QMessageBox.warning(dialog, "Duplicate", f"Medical centre '{name}' already exists.")
                    return
                if any(c.reference.upper() == reference.upper() for c in existing):
                    QMessageBox.warning(dialog, "Duplicate", f"Reference '{reference}' already exists.")
                    return
                
                # Create new medical centre
                new_centre = MedicalCentre(
                    name=name,
                    reference=reference,
                    address=address,
                    contact_person=contact,
                    phone=phone
                )
                self.db_manager.add(new_centre)
                
                # Reload dropdown
                self.load_dropdown_data()
                
                # Select the newly added centre
                index = self.medical_centre_combo.findText(name)
                if index >= 0:
                    self.medical_centre_combo.setCurrentIndex(index)
                
                QMessageBox.information(dialog, "Success", f"Medical centre '{name}' added successfully!")
                dialog.accept()
                
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to add medical centre:\n{str(e)}")
        
        save_btn.clicked.connect(save_centre)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def quick_add_distribution_location(self):
        """Quick add a new distribution location with full form."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Distribution Location")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel("➕ Add New Distribution Location")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter distribution location name")
        form_layout.addRow("Name: *", name_input)
        
        reference_input = QLineEdit()
        reference_input.setPlaceholderText("Enter reference code (e.g., DL-001)")
        form_layout.addRow("Reference: *", reference_input)
        
        address_input = QLineEdit()
        address_input.setPlaceholderText("Enter address (optional)")
        form_layout.addRow("Address:", address_input)
        
        contact_input = QLineEdit()
        contact_input.setPlaceholderText("Enter contact person name (optional)")
        form_layout.addRow("Contact Person:", contact_input)
        
        phone_input = QLineEdit()
        phone_input.setPlaceholderText("Enter phone number (optional)")
        form_layout.addRow("Phone:", phone_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet("""
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
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        def save_location():
            name = sanitize_input(name_input.text().strip())
            reference = sanitize_input(reference_input.text().strip().upper())
            address = sanitize_input(address_input.text().strip()) or None
            contact = sanitize_input(contact_input.text().strip()) or None
            phone = sanitize_input(phone_input.text().strip()) or None
            
            # Validation
            if not name:
                QMessageBox.warning(dialog, "Validation Error", "Name cannot be empty.")
                return
            if not reference:
                QMessageBox.warning(dialog, "Validation Error", "Reference cannot be empty.")
                return
            
            try:
                # Check if already exists
                existing = self.db_manager.get_all(DistributionLocation)
                if any(l.name.lower() == name.lower() for l in existing):
                    QMessageBox.warning(dialog, "Duplicate", f"Distribution location '{name}' already exists.")
                    return
                if any(l.reference.upper() == reference.upper() for l in existing):
                    QMessageBox.warning(dialog, "Duplicate", f"Reference '{reference}' already exists.")
                    return
                
                # Create new distribution location
                new_location = DistributionLocation(
                    name=name,
                    reference=reference,
                    address=address,
                    contact_person=contact,
                    phone=phone
                )
                self.db_manager.add(new_location)
                
                # Reload dropdown
                self.load_dropdown_data()
                
                # Select the newly added location
                index = self.distribution_location_combo.findText(name)
                if index >= 0:
                    self.distribution_location_combo.setCurrentIndex(index)
                
                QMessageBox.information(dialog, "Success", f"Distribution location '{name}' added successfully!")
                dialog.accept()
                
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to add distribution location:\n{str(e)}")
        
        save_btn.clicked.connect(save_location)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
