"""
Pharmacy Dialog - Add/Edit Pharmacy
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.database import Pharmacy
from src.database.db_manager import DatabaseManager
from src.utils import sanitize_input, validate_reference


class PharmacyDialog(QDialog):
    """Dialog for adding or editing a pharmacy."""
    
    pharmacy_saved = pyqtSignal()
    
    def __init__(self, db_manager: DatabaseManager, pharmacy: Pharmacy = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.pharmacy = pharmacy
        self.is_edit_mode = pharmacy is not None
        
        self.setWindowTitle("Edit Pharmacy" if self.is_edit_mode else "Add Pharmacy")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.setup_ui()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Form
        form_layout = QFormLayout()
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter pharmacy name")
        self.name_input.setMaxLength(100)
        form_layout.addRow("Name*:", self.name_input)
        
        # Reference
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Enter reference code (will be auto-uppercase)")
        self.reference_input.setMaxLength(50)
        form_layout.addRow("Reference:", self.reference_input)
        
        # TRN (Tax Registration Number)
        self.trn_input = QLineEdit()
        self.trn_input.setPlaceholderText("Enter Tax Registration Number")
        self.trn_input.setMaxLength(100)
        form_layout.addRow("TRN:", self.trn_input)
        
        # Contact Person
        self.contact_person_input = QLineEdit()
        self.contact_person_input.setPlaceholderText("Enter contact person name")
        self.contact_person_input.setMaxLength(100)
        form_layout.addRow("Contact Person:", self.contact_person_input)
        
        # Phone
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number")
        self.phone_input.setMaxLength(20)
        form_layout.addRow("Phone:", self.phone_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        self.email_input.setMaxLength(100)
        form_layout.addRow("Email:", self.email_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any additional notes")
        self.notes_input.setMaximumHeight(100)
        form_layout.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Required fields note
        note_label = QLabel("* Required fields")
        note_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(note_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_pharmacy)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Focus on name input
        self.name_input.setFocus()
    
    def populate_fields(self):
        """Populate fields with pharmacy data."""
        if not self.pharmacy:
            return
        
        self.name_input.setText(self.pharmacy.name)
        if self.pharmacy.reference:
            self.reference_input.setText(self.pharmacy.reference)
        
        if self.pharmacy.trn:
            self.trn_input.setText(self.pharmacy.trn)
        
        if self.pharmacy.contact_person:
            self.contact_person_input.setText(self.pharmacy.contact_person)
        
        if self.pharmacy.phone:
            self.phone_input.setText(self.pharmacy.phone)
        
        if self.pharmacy.email:
            self.email_input.setText(self.pharmacy.email)
        
        if self.pharmacy.notes:
            self.notes_input.setPlainText(self.pharmacy.notes)
    
    def save_pharmacy(self):
        """Save the pharmacy."""
        # Get values
        name = sanitize_input(self.name_input.text())
        reference = sanitize_input(self.reference_input.text())
        trn = sanitize_input(self.trn_input.text())
        contact_person = sanitize_input(self.contact_person_input.text())
        phone = sanitize_input(self.phone_input.text())
        email = sanitize_input(self.email_input.text())
        notes = self.notes_input.toPlainText().strip()
        
        # Validate required fields
        if not name:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            self.name_input.setFocus()
            return
        
        # Validate reference format if provided
        if reference and not validate_reference(reference):
            QMessageBox.warning(
                self, "Validation Error",
                "Reference must contain only letters, numbers, hyphens, and underscores."
            )
            self.reference_input.setFocus()
            return
        
        # Normalize reference to uppercase if provided
        if reference:
            reference = reference.upper()
        else:
            reference = None
        
        try:
            with self.db_manager.get_session() as session:
                if self.is_edit_mode:
                    # Update existing pharmacy
                    self.pharmacy.name = name
                    self.pharmacy.reference = reference if reference else None
                    self.pharmacy.trn = trn if trn else None
                    self.pharmacy.contact_person = contact_person if contact_person else None
                    self.pharmacy.phone = phone if phone else None
                    self.pharmacy.email = email if email else None
                    self.pharmacy.notes = notes if notes else None
                    
                    session.add(self.pharmacy)
                    session.commit()
                    
                    QMessageBox.information(self, "Success", "Pharmacy updated successfully.")
                else:
                    # Check for duplicate name
                    existing = session.query(Pharmacy).filter(
                        Pharmacy.name == name
                    ).first()
                    
                    if existing:
                        QMessageBox.warning(
                            self, "Duplicate Entry",
                            f"A pharmacy with the name '{name}' already exists."
                        )
                        self.name_input.setFocus()
                        return
                    
                    # Check for duplicate reference if provided
                    if reference:
                        existing = session.query(Pharmacy).filter(
                            Pharmacy.reference == reference
                        ).first()
                        
                        if existing:
                            QMessageBox.warning(
                                self, "Duplicate Entry",
                                f"A pharmacy with the reference '{reference}' already exists."
                            )
                            self.reference_input.setFocus()
                            return
                    
                    # Create new pharmacy
                    new_pharmacy = Pharmacy(
                        name=name,
                        reference=reference if reference else None,
                        trn=trn if trn else None,
                        contact_person=contact_person if contact_person else None,
                        phone=phone if phone else None,
                        email=email if email else None,
                        notes=notes if notes else None
                    )
                    
                    session.add(new_pharmacy)
                    session.commit()
                    
                    QMessageBox.information(self, "Success", "Pharmacy created successfully.")
                
                self.pharmacy_saved.emit()
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save pharmacy: {str(e)}")
