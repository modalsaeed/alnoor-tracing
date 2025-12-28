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
from src.utils.model_helpers import get_attr


class CouponDialog(QDialog):
    """Dialog for adding or editing a patient coupon."""

    def quick_add_medical_centre(self):
        """Quick add a new medical centre with full form (matches MedicalCentreDialog)."""
        from src.utils import validate_name, validate_reference, validate_phone, sanitize_input, normalize_reference
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Medical Centre")
        dialog.setMinimumWidth(550)

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
        reference_input.setPlaceholderText("Enter unique reference (e.g., MC-001)")
        form_layout.addRow("Reference:", reference_input)

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

        # Required fields note
        note = QLabel("* Required fields")
        note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(note)

        layout.addSpacing(20)

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

        def is_reference_duplicate(reference: str) -> bool:
            try:
                all_centres = self.db_manager.get_all(MedicalCentre)
                from src.utils.model_helpers import get_attr
                existing = next((c for c in all_centres if get_attr(c, 'reference') == reference.upper()), None)
                return existing is not None
            except Exception:
                return False

        def save_centre():
            name = sanitize_input(name_input.text().strip())
            reference = sanitize_input(reference_input.text().strip())
            address = sanitize_input(address_input.text().strip()) or None
            contact = sanitize_input(contact_input.text().strip()) or None
            phone = sanitize_input(phone_input.text().strip()) or None

            # Validation
            is_valid, error_msg = validate_name(name, min_length=2, field_name="Medical centre name")
            if not is_valid:
                QMessageBox.warning(dialog, "Validation Error", error_msg)
                return
            if reference:
                is_valid, error_msg = validate_reference(reference, min_length=2)
                if not is_valid:
                    QMessageBox.warning(dialog, "Validation Error", f"Medical centre reference error: {error_msg}")
                    return
            if phone:
                is_valid, error_msg = validate_phone(phone)
                if not is_valid:
                    QMessageBox.warning(dialog, "Validation Error", f"Phone error: {error_msg}")
                    return
            # Normalize reference if provided
            if reference:
                reference_normalized = normalize_reference(reference)
                if is_reference_duplicate(reference_normalized):
                    QMessageBox.warning(dialog, "Validation Error", f"Reference '{reference_normalized}' already exists. Please use a unique reference.")
                    return

            # Save
            try:
                from src.database.models import MedicalCentre
                new_centre = MedicalCentre(
                    name=name,
                    reference=reference.upper() if reference else None,
                    address=address if address else None,
                    contact_person=contact if contact else None,
                    phone=phone if phone else None
                )
                self.db_manager.add(new_centre)
                QMessageBox.information(dialog, "Success", f"Medical centre '{name}' added successfully!")
                dialog.accept()
                self.load_dropdown_data()  # Refresh dropdowns
            except Exception as e:
                QMessageBox.critical(dialog, "Error Saving Centre", f"Failed to save medical centre:\n{str(e)}")

        save_btn.clicked.connect(save_centre)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()
    
    def __init__(self, db_manager: DatabaseManager, coupon: Optional[PatientCoupon] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.coupon = coupon
        self.is_edit_mode = coupon is not None
        self.products = []
        self.medical_centres = []
        self.distribution_locations = []
        self.setup_ui()
        self.load_dropdown_data()
        if self.is_edit_mode:
            self.populate_fields()

    def setup_ui(self):
        """Modern, user-friendly UI for coupon dialog, with quick-add for health centre and distribution location."""
        self.setWindowTitle("Add/Edit Patient Coupon")
        self.setMinimumWidth(600)
        self.setMinimumHeight(420)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("🏷️ Add/Edit Patient Coupon")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel("Fill in coupon details. Use ➕ to quickly add a new health centre or distribution location if needed.")
        instructions.setStyleSheet("color: #6c757d; margin-bottom: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Form
        form_layout = QFormLayout()

        # Coupon Reference
        self.coupon_ref_input = QLineEdit()
        self.coupon_ref_input.setPlaceholderText("Enter coupon reference (e.g., CP-001)")
        form_layout.addRow("Coupon Reference: *", self.coupon_ref_input)

        # Patient Name
        self.patient_name_input = QLineEdit()
        self.patient_name_input.setPlaceholderText("Enter patient name (optional)")
        form_layout.addRow("Patient Name:", self.patient_name_input)

        # CPR
        self.cpr_input = QLineEdit()
        self.cpr_input.setPlaceholderText("Enter CPR (optional)")
        form_layout.addRow("CPR:", self.cpr_input)

        # Date Received
        self.date_received_input = QDateEdit()
        self.date_received_input.setCalendarPopup(True)
        self.date_received_input.setDate(QDate.currentDate())
        self.date_received_input.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Date Received: *", self.date_received_input)

        # Product dropdown
        self.product_combo = QComboBox()
        form_layout.addRow("Product: *", self.product_combo)

        # Product Reference display
        self.product_ref_display = QLabel("")
        self.product_ref_display.setStyleSheet("color: #888; font-size: 11px;")
        form_layout.addRow("Product Reference:", self.product_ref_display)

        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(1)
        self.quantity_input.setSuffix(" pieces")
        form_layout.addRow("Quantity: *", self.quantity_input)

        # MOH Health Centre with quick add
        mc_layout = QHBoxLayout()
        self.medical_centre_combo = QComboBox()
        mc_layout.addWidget(self.medical_centre_combo, 1)
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
        mc_layout.addWidget(add_centre_btn)
        form_layout.addRow("MOH Health Centre: *", mc_layout)

        # Distribution Location with quick add
        dl_layout = QHBoxLayout()
        self.distribution_location_combo = QComboBox()
        dl_layout.addWidget(self.distribution_location_combo, 1)
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
        dl_layout.addWidget(add_location_btn)
        form_layout.addRow("Distribution Location: *", dl_layout)

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
        note = QLabel("* Required fields | Patient info is optional")
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
    
    def quick_add_distribution_location(self):
        """Quick add a new distribution location with full form (matches DistributionLocationDialog)."""
        from src.utils import validate_name, validate_reference, validate_phone, sanitize_input, normalize_reference
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Distribution Location")
        dialog.setMinimumWidth(550)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("➕ Add New Distribution Location")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter location name")
        form_layout.addRow("Name: *", name_input)

        reference_input = QLineEdit()
        reference_input.setPlaceholderText("Enter unique reference (e.g., LOC-001)")
        form_layout.addRow("Reference:", reference_input)

        trn_input = QLineEdit()
        trn_input.setPlaceholderText("Enter Tax Registration Number")
        trn_input.setMaxLength(100)
        form_layout.addRow("TRN:", trn_input)

        # No pharmacy selection in quick add (for simplicity)

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

        # Required fields note
        note = QLabel("* Required fields")
        note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(note)

        layout.addSpacing(20)

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

        def is_reference_duplicate(reference: str) -> bool:
            try:
                all_locations = self.db_manager.get_all(DistributionLocation)
                from src.utils.model_helpers import get_attr
                existing = next((l for l in all_locations if get_attr(l, 'reference') == reference.upper()), None)
                return existing is not None
            except Exception:
                return False

        def save_location():
            name = sanitize_input(name_input.text().strip())
            reference = sanitize_input(reference_input.text().strip())
            trn = sanitize_input(trn_input.text().strip()) or None
            address = sanitize_input(address_input.text().strip()) or None
            contact = sanitize_input(contact_input.text().strip()) or None
            phone = sanitize_input(phone_input.text().strip()) or None

            # Validation
            is_valid, error_msg = validate_name(name, min_length=2, field_name="Location name")
            if not is_valid:
                QMessageBox.warning(dialog, "Validation Error", error_msg)
                return
            if reference:
                is_valid, error_msg = validate_reference(reference, min_length=2)
                if not is_valid:
                    QMessageBox.warning(dialog, "Validation Error", f"Location reference error: {error_msg}")
                    return
            if phone:
                is_valid, error_msg = validate_phone(phone)
                if not is_valid:
                    QMessageBox.warning(dialog, "Validation Error", f"Phone error: {error_msg}")
                    return
            # Normalize reference if provided
            if reference:
                reference_normalized = normalize_reference(reference)
                if is_reference_duplicate(reference_normalized):
                    QMessageBox.warning(dialog, "Validation Error", f"Reference '{reference_normalized}' already exists. Please use a unique reference.")
                    return

            # Save
            try:
                from src.database.models import DistributionLocation
                new_location = DistributionLocation(
                    name=name,
                    reference=reference.upper() if reference else None,
                    trn=trn if trn else None,
                    address=address if address else None,
                    contact_person=contact if contact else None,
                    phone=phone if phone else None,
                    pharmacy_id=None  # No pharmacy selection in quick add
                )
                self.db_manager.add(new_location)
                QMessageBox.information(dialog, "Success", f"Distribution location '{name}' added successfully!")
                dialog.accept()
                self.load_dropdown_data()  # Refresh dropdowns
            except Exception as e:
                QMessageBox.critical(dialog, "Error Saving Location", f"Failed to save distribution location:\n{str(e)}")

        save_btn.clicked.connect(save_location)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()
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
            from src.utils.model_helpers import get_name, get_id
            for product in self.products:
                self.product_combo.addItem(f"{get_name(product)}", get_id(product))
            
            # Load medical centres with autocomplete
            self.medical_centres = self.db_manager.get_all(MedicalCentre)
            self.medical_centre_combo.clear()
            self.medical_centre_combo.addItem("-- Select MOH Health Centre --", None)
            centre_names = []
            for centre in self.medical_centres:
                from src.utils.model_helpers import get_name, get_id
                self.medical_centre_combo.addItem(get_name(centre), get_id(centre))
                centre_names.append(get_name(centre))
            
            # Setup autocomplete for medical centres
            if centre_names:
                self.medical_centre_combo.setEditable(True)
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
                from src.utils.model_helpers import get_name, get_id
                self.distribution_location_combo.addItem(get_name(location), get_id(location))
                location_names.append(get_name(location))
            
            # Setup autocomplete for distribution locations
            if location_names:
                self.distribution_location_combo.setEditable(True)
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
            # Find the product (dict/ORM safe)
            from src.utils.model_helpers import get_attr
            product = next((p for p in self.products if get_attr(p, 'id') == product_id), None)
            if product:
                self.product_ref_display.setText(get_attr(product, 'reference', ''))

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
            from src.utils.model_helpers import get_attr
            self.coupon_ref_input.setText(get_attr(self.coupon, 'coupon_reference', ''))

            # Handle optional patient fields
            patient_name = get_attr(self.coupon, 'patient_name', '')
            if patient_name:
                self.patient_name_input.setText(patient_name)

            cpr = get_attr(self.coupon, 'cpr', '')
            if cpr:
                self.cpr_input.setText(cpr)

            # Set date received
            date_val = get_attr(self.coupon, 'date_received', None)
            if date_val:
                import datetime as dt
                if isinstance(date_val, dt.datetime):
                    date = date_val
                elif isinstance(date_val, str):
                    try:
                        date = dt.datetime.fromisoformat(date_val)
                    except Exception:
                        date = None
                else:
                    date = None
                if date:
                    qdate = QDate(date.year, date.month, date.day)
                    self.date_received_input.setDate(qdate)

            # Select product
            product_id = get_attr(self.coupon, 'product_id', None)
            for i in range(self.product_combo.count()):
                if self.product_combo.itemData(i) == product_id:
                    self.product_combo.setCurrentIndex(i)
                    break

            self.quantity_input.setValue(get_attr(self.coupon, 'quantity_pieces', 0))

            # Select medical centre
            medical_centre_id = get_attr(self.coupon, 'medical_centre_id', None)
            for i in range(self.medical_centre_combo.count()):
                if self.medical_centre_combo.itemData(i) == medical_centre_id:
                    self.medical_centre_combo.setCurrentIndex(i)
                    break

            # Select distribution location
            distribution_location_id = get_attr(self.coupon, 'distribution_location_id', None)
            for i in range(self.distribution_location_combo.count()):
                if self.distribution_location_combo.itemData(i) == distribution_location_id:
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
            is_api = hasattr(self.db_manager, 'is_api_client') and getattr(self.db_manager, 'is_api_client', False)

            if self.is_edit_mode and self.coupon:
                # Update the coupon object (dict or ORM)
                from src.utils.model_helpers import get_attr
                if isinstance(self.coupon, dict):
                    self.coupon['coupon_reference'] = coupon_reference
                    self.coupon['patient_name'] = patient_name
                    self.coupon['cpr'] = cpr
                    self.coupon['product_id'] = product_id
                    self.coupon['quantity_pieces'] = quantity
                    self.coupon['medical_centre_id'] = medical_centre_id
                    self.coupon['distribution_location_id'] = distribution_location_id
                    self.coupon['date_received'] = date_received.isoformat() if is_api else date_received
                    # API update call if needed (not shown here)
                else:
                    self.coupon.coupon_reference = coupon_reference
                    self.coupon.patient_name = patient_name
                    self.coupon.cpr = cpr
                    self.coupon.product_id = product_id
                    self.coupon.quantity_pieces = quantity
                    self.coupon.medical_centre_id = medical_centre_id
                    self.coupon.distribution_location_id = distribution_location_id
                    self.coupon.date_received = date_received
                # Save/update in DB
                self.db_manager.update(self.coupon)
                patient_info = f"for {patient_name}" if patient_name else ""
                QMessageBox.information(
                    self,
                    "Success",
                    f"Coupon {coupon_reference} {patient_info} updated successfully!"
                )
                self.accept()
            else:
                # Create new coupon
                coupon_data = dict(
                    coupon_reference=coupon_reference,
                    patient_name=patient_name,
                    cpr=cpr,
                    product_id=product_id,
                    quantity_pieces=quantity,
                    medical_centre_id=medical_centre_id,
                    distribution_location_id=distribution_location_id,
                    verified=False,  # Initially not verified
                    date_received=date_received.isoformat() if is_api else date_received
                )
                # ORM: create PatientCoupon, API: send dict
                if is_api:
                    # API create call if needed (not shown here)
                    pass
                else:
                    new_coupon = PatientCoupon(**coupon_data)
                    self.db_manager.add(new_coupon)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Coupon {coupon_reference} created successfully!"
                )
                self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Coupon",
                f"Failed to save coupon:\n{str(e)}"
            )
    
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
