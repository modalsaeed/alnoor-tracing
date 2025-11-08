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
)
from PyQt6.QtCore import Qt

from database import DatabaseManager, DistributionLocation


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
    
    def populate_fields(self):
        """Populate form fields with existing location data."""
        if self.location:
            self.name_input.setText(self.location.name)
            self.reference_input.setText(self.location.reference)
            if self.location.address:
                self.address_input.setPlainText(self.location.address)
            if self.location.contact_person:
                self.contact_input.setText(self.location.contact_person)
            if self.location.phone:
                self.phone_input.setText(self.location.phone)
    
    def validate_input(self) -> tuple[bool, str]:
        """
        Validate user input.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        name = self.name_input.text().strip()
        reference = self.reference_input.text().strip()
        
        if not name:
            return False, "Location name is required."
        
        if not reference:
            return False, "Location reference is required."
        
        if len(name) < 2:
            return False, "Location name must be at least 2 characters."
        
        if len(reference) < 2:
            return False, "Location reference must be at least 2 characters."
        
        # Check for duplicate reference
        if not self.is_edit_mode or (self.location and reference.upper() != self.location.reference):
            if self.is_reference_duplicate(reference):
                return False, f"Reference '{reference.upper()}' already exists. Please use a unique reference."
        
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
            
            if self.is_edit_mode:
                # Update existing location
                self.location.name = name
                self.location.reference = reference.upper()
                self.location.address = address if address else None
                self.location.contact_person = contact_person if contact_person else None
                self.location.phone = phone if phone else None
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
                    phone=phone if phone else None
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
