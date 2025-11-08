"""
Medical Centre Dialog - Add/Edit dialog for medical centre management.

Provides a form for creating new medical centres or editing existing ones.
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
)
from PyQt6.QtCore import Qt

from database import DatabaseManager, MedicalCentre
from utils import validate_name, validate_reference, validate_phone, sanitize_input, normalize_reference


class MedicalCentreDialog(QDialog):
    """Dialog for adding or editing a medical centre."""
    
    def __init__(self, db_manager: DatabaseManager, centre: Optional[MedicalCentre] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.centre = centre
        self.is_edit_mode = centre is not None
        
        self.init_ui()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Edit Medical Centre" if self.is_edit_mode else "Add New Medical Centre")
        self.setMinimumWidth(550)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("✏️ Edit Medical Centre" if self.is_edit_mode else "➕ Add New Medical Centre")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        # Centre Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter medical centre name")
        form_layout.addRow("Name: *", self.name_input)
        
        # Centre Reference
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Enter unique reference (e.g., MC-001)")
        form_layout.addRow("Reference: *", self.reference_input)
        
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
        
        self.save_btn = QPushButton("Update" if self.is_edit_mode else "Add Centre")
        self.save_btn.clicked.connect(self.save_centre)
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
    
    def populate_fields(self):
        """Populate form fields with existing centre data."""
        if self.centre:
            self.name_input.setText(self.centre.name)
            self.reference_input.setText(self.centre.reference)
            if self.centre.address:
                self.address_input.setPlainText(self.centre.address)
            if self.centre.contact_person:
                self.contact_input.setText(self.centre.contact_person)
            if self.centre.phone:
                self.phone_input.setText(self.centre.phone)
    
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
        
        # Validate medical centre name
        is_valid, error_msg = validate_name(name, min_length=2, field_name="Medical centre name")
        if not is_valid:
            return False, error_msg
        
        # Validate medical centre reference
        is_valid, error_msg = validate_reference(reference, min_length=2)
        if not is_valid:
            return False, f"Medical centre reference error: {error_msg}"
        
        # Validate phone if provided
        if phone:
            is_valid, error_msg = validate_phone(phone)
            if not is_valid:
                return False, f"Phone error: {error_msg}"
        
        # Normalize reference
        reference_normalized = normalize_reference(reference)
        
        # Check for duplicate reference
        if not self.is_edit_mode or (self.centre and reference_normalized != self.centre.reference):
            if self.is_reference_duplicate(reference_normalized):
                return False, f"Reference '{reference_normalized}' already exists. Please use a unique reference."
        
        return True, ""
    
    def is_reference_duplicate(self, reference: str) -> bool:
        """Check if reference already exists in database."""
        try:
            with self.db_manager.get_session() as session:
                existing = session.query(MedicalCentre).filter(
                    MedicalCentre.reference == reference.upper()
                ).first()
                return existing is not None
        except Exception:
            return False
    
    def save_centre(self):
        """Save the medical centre to database."""
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
            
            if self.is_edit_mode:
                # Update existing centre
                self.centre.name = name
                self.centre.reference = reference.upper()
                self.centre.address = address if address else None
                self.centre.contact_person = contact_person if contact_person else None
                self.centre.phone = phone if phone else None
                self.db_manager.update(self.centre)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Medical centre '{name}' updated successfully!"
                )
            else:
                # Create new centre
                new_centre = MedicalCentre(
                    name=name,
                    reference=reference.upper(),
                    address=address if address else None,
                    contact_person=contact_person if contact_person else None,
                    phone=phone if phone else None
                )
                self.db_manager.add(new_centre)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Medical centre '{name}' added successfully!"
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Centre",
                f"Failed to save medical centre:\n{str(e)}"
            )
