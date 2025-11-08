"""
Product Dialog - Add/Edit dialog for product management.

Provides a form for creating new products or editing existing ones.
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

from src.database.db_manager import DatabaseManager
from src.database.models import Product
from src.utils import validate_name, validate_reference, sanitize_input, normalize_reference


class ProductDialog(QDialog):
    """Dialog for adding or editing a product."""
    
    def __init__(self, db_manager: DatabaseManager, product: Optional[Product] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.product = product  # None for new product, Product instance for editing
        self.is_edit_mode = product is not None
        
        self.init_ui()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Edit Product" if self.is_edit_mode else "Add New Product")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("✏️ Edit Product" if self.is_edit_mode else "➕ Add New Product")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        # Product Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter product name")
        form_layout.addRow("Name: *", self.name_input)
        
        # Product Reference
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Enter unique reference (e.g., PROD-001)")
        form_layout.addRow("Reference: *", self.reference_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter product description (optional)")
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_input)
        
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
        
        self.save_btn = QPushButton("Update" if self.is_edit_mode else "Add Product")
        self.save_btn.clicked.connect(self.save_product)
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
        """Populate form fields with existing product data."""
        if self.product:
            self.name_input.setText(self.product.name)
            self.reference_input.setText(self.product.reference)
            if self.product.description:
                self.description_input.setPlainText(self.product.description)
    
    def validate_input(self) -> tuple[bool, str]:
        """
        Validate user input using centralized validators.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Sanitize inputs
        name = sanitize_input(self.name_input.text())
        reference = sanitize_input(self.reference_input.text())
        
        # Validate product name
        is_valid, error_msg = validate_name(name, min_length=2, max_length=100)
        if not is_valid:
            return False, f"Product name error: {error_msg}"
        
        # Validate product reference
        is_valid, error_msg = validate_reference(reference, min_length=2)
        if not is_valid:
            return False, f"Product reference error: {error_msg}"
        
        # Normalize reference for consistency
        reference_normalized = normalize_reference(reference)
        
        # Check for duplicate reference (only if creating new or reference changed)
        if not self.is_edit_mode or (self.product and reference_normalized != self.product.reference):
            if self.is_reference_duplicate(reference_normalized):
                return False, f"Reference '{reference_normalized}' already exists. Please use a unique reference."
        
        return True, ""
    
    def is_reference_duplicate(self, reference: str) -> bool:
        """Check if reference already exists in database."""
        try:
            with self.db_manager.get_session() as session:
                existing = session.query(Product).filter(
                    Product.reference == reference.upper()
                ).first()
                return existing is not None
        except Exception:
            return False
    
    def save_product(self):
        """Save the product to database."""
        # Validate input
        is_valid, error_msg = self.validate_input()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        try:
            # Sanitize and normalize inputs
            name = sanitize_input(self.name_input.text())
            reference = normalize_reference(sanitize_input(self.reference_input.text()))
            description = sanitize_input(self.description_input.toPlainText())
            
            if self.is_edit_mode:
                # Update existing product
                self.product.name = name
                self.product.reference = reference
                self.product.description = description if description else None
                self.db_manager.update(self.product)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Product '{name}' updated successfully!"
                )
            else:
                # Create new product
                new_product = Product(
                    name=name,
                    reference=reference,
                    description=description if description else None
                )
                self.db_manager.add(new_product)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Product '{name}' added successfully!"
                )
            
            self.accept()  # Close dialog with success
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Product",
                f"Failed to save product:\n{str(e)}"
            )
