"""
Distribution Location Dialog - Add/Edit dialog for distribution location management.

Provides a form for creating new distribution locations or editing existing ones.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QComboBox,
)
from PyQt6.QtCore import Qt

from src.database.db_manager import DatabaseManager
from src.database.models import DistributionLocation, Pharmacy
from src.utils import validate_name, validate_reference, validate_phone, sanitize_input, normalize_reference


class DistributionLocationDialog(QDialog):
    """Dialog for adding or editing a distribution location."""
    
    def __init__(self, db_manager: DatabaseManager, location: Optional[DistributionLocation] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.location = location
        self.is_edit_mode = location is not None
        
        self.init_ui()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Edit Distribution Location" if self.is_edit_mode else "Add New Distribution Location")
        self.setMinimumWidth(550)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("✏️ Edit Location" if self.is_edit_mode else "➕ Add New Distribution Location")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        # Location Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter location name")
        form_layout.addRow("Name: *", self.name_input)
        
        # Location Reference
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Enter unique reference (e.g., LOC-001)")
        form_layout.addRow("Reference: *", self.reference_input)
        
        # Pharmacy (optional grouping)
        self.pharmacy_combo = QComboBox()
        self.pharmacy_combo.addItem("None", None)  # No pharmacy selected
        self.load_pharmacies()
        form_layout.addRow("Pharmacy:", self.pharmacy_combo)
        
        # Address
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Enter full address")
        self.address_input.setMaximumHeight(80)
        form_layout.addRow("Address:", self.address_input)
        
        # Contact Person
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Enter contact person name")
        form_layout.addRow("Contact Person:", self.contact_input)
        
        # Phone
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number")
        form_layout.addRow("Phone:", self.phone_input)
        
        layout.addLayout(form_layout)
        
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
        
        self.save_btn = QPushButton("Update" if self.is_edit_mode else "Add Location")
        self.save_btn.clicked.connect(self.save_location)
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
    
    def load_pharmacies(self):
        """Load pharmacies into the combo box."""
        try:
            with self.db_manager.get_session() as session:
                pharmacies = session.query(Pharmacy).order_by(Pharmacy.name).all()
                
                for pharmacy in pharmacies:
                    self.pharmacy_combo.addItem(pharmacy.name, pharmacy.id)
        except Exception as e:
            print(f"Error loading pharmacies: {e}")
    
    def populate_fields(self):
        """Populate form fields with existing location data."""
        if self.location:
            self.name_input.setText(self.location.name)
            self.reference_input.setText(self.location.reference)
            
            # Set pharmacy if assigned
            if self.location.pharmacy_id:
                for i in range(self.pharmacy_combo.count()):
                    if self.pharmacy_combo.itemData(i) == self.location.pharmacy_id:
                        self.pharmacy_combo.setCurrentIndex(i)
                        break
            
            if self.location.address:
                self.address_input.setPlainText(self.location.address)
            if self.location.contact_person:
                self.contact_input.setText(self.location.contact_person)
            if self.location.phone:
                self.phone_input.setText(self.location.phone)
    
    def validate_input(self) -> tuple[bool, str]:
        """
        Validate user input using centralized validators.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Sanitize inputs
        name = sanitize_input(self.name_input.text())
        reference = sanitize_input(self.reference_input.text())
        phone = sanitize_input(self.phone_input.text()) if hasattr(self, 'phone_input') else ""
        
        # Validate location name
        is_valid, error_msg = validate_name(name, min_length=2, field_name="Location name")
        if not is_valid:
            return False, error_msg
        
        # Validate location reference
        is_valid, error_msg = validate_reference(reference, min_length=2)
        if not is_valid:
            return False, f"Location reference error: {error_msg}"
        
        # Validate phone if provided
        if phone:
            is_valid, error_msg = validate_phone(phone)
            if not is_valid:
                return False, f"Phone error: {error_msg}"
        
        # Normalize reference
        reference_normalized = normalize_reference(reference)
        
        # Check for duplicate reference
        if not self.is_edit_mode or (self.location and reference_normalized != self.location.reference):
            if self.is_reference_duplicate(reference_normalized):
                return False, f"Reference '{reference_normalized}' already exists. Please use a unique reference."
        
        return True, ""
    
    def is_reference_duplicate(self, reference: str) -> bool:
        """Check if reference already exists in database."""
        try:
            with self.db_manager.get_session() as session:
                existing = session.query(DistributionLocation).filter(
                    DistributionLocation.reference == reference.upper()
                ).first()
                return existing is not None
        except Exception:
            return False
    
    def save_location(self):
        """Save the distribution location to database."""
        # Validate input
        is_valid, error_msg = self.validate_input()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        try:
            name = self.name_input.text().strip()
            reference = self.reference_input.text().strip()
            address = self.address_input.toPlainText().strip()
            contact_person = self.contact_input.text().strip()
            phone = self.phone_input.text().strip()
            
            # Get selected pharmacy ID (None if "None" is selected)
            pharmacy_id = self.pharmacy_combo.currentData()
            
            if self.is_edit_mode:
                # Update existing location
                self.location.name = name
                self.location.reference = reference.upper()
                self.location.address = address if address else None
                self.location.contact_person = contact_person if contact_person else None
                self.location.phone = phone if phone else None
                self.location.pharmacy_id = pharmacy_id
                self.db_manager.update(self.location)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Distribution location '{name}' updated successfully!"
                )
            else:
                # Create new location
                new_location = DistributionLocation(
                    name=name,
                    reference=reference.upper(),
                    address=address if address else None,
                    contact_person=contact_person if contact_person else None,
                    phone=phone if phone else None,
                    pharmacy_id=pharmacy_id
                )
                self.db_manager.add(new_location)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Distribution location '{name}' added successfully!"
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Location",
                f"Failed to save distribution location:\n{str(e)}"
            )
