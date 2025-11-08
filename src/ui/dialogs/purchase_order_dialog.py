"""
Purchase Order Dialog - Add/Edit dialog for purchase order management.

Provides a form for creating new purchase orders or editing existing ones.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from src.database.db_manager import DatabaseManager
from src.database.models import PurchaseOrder, Product
from src.utils import validate_po_reference, validate_quantity, sanitize_input, normalize_reference


class PurchaseOrderDialog(QDialog):
    """Dialog for adding or editing a purchase order."""
    
    def __init__(self, db_manager: DatabaseManager, order: Optional[PurchaseOrder] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.order = order
        self.is_edit_mode = order is not None
        self.products = []
        
        self.init_ui()
        self.load_products()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Edit Purchase Order" if self.is_edit_mode else "Add New Purchase Order")
        self.setMinimumWidth(550)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("✏️ Edit Purchase Order" if self.is_edit_mode else "➕ Add New Purchase Order")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        # PO Reference
        self.po_reference_input = QLineEdit()
        self.po_reference_input.setPlaceholderText("Enter PO reference (e.g., PO-2024-001)")
        form_layout.addRow("PO Reference: *", self.po_reference_input)
        
        # Product Selection (dropdown)
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        form_layout.addRow("Product: *", self.product_combo)
        
        # Product Description (auto-filled, read-only)
        self.product_desc_display = QLineEdit()
        self.product_desc_display.setReadOnly(True)
        self.product_desc_display.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("Product Ref:", self.product_desc_display)
        
        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1000000)
        self.quantity_input.setValue(100)
        self.quantity_input.setSuffix(" units")
        form_layout.addRow("Quantity: *", self.quantity_input)
        
        # Warehouse Location
        self.warehouse_input = QLineEdit()
        self.warehouse_input.setPlaceholderText("Enter warehouse location (optional)")
        form_layout.addRow("Warehouse:", self.warehouse_input)
        
        layout.addLayout(form_layout)
        
        # Stock info (for edit mode)
        if self.is_edit_mode:
            self.stock_info_label = QLabel()
            self.stock_info_label.setStyleSheet(
                "background-color: #e3f2fd; padding: 10px; border-radius: 4px; "
                "color: #1976d2; font-weight: bold;"
            )
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
        
        self.save_btn = QPushButton("Update" if self.is_edit_mode else "Add Order")
        self.save_btn.clicked.connect(self.save_order)
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
    
    def load_products(self):
        """Load products into dropdown."""
        try:
            self.products = self.db_manager.get_all(Product)
            
            self.product_combo.clear()
            self.product_combo.addItem("-- Select Product --", None)
            
            for product in self.products:
                self.product_combo.addItem(
                    f"{product.name} ({product.reference})",
                    product.id
                )
            
            if not self.products:
                QMessageBox.warning(
                    self,
                    "No Products",
                    "No products found in database.\nPlease add products first."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Products",
                f"Failed to load products:\n{str(e)}"
            )
    
    def on_product_changed(self, index):
        """Handle product selection change."""
        product_id = self.product_combo.currentData()
        
        if product_id:
            # Find the product
            product = next((p for p in self.products if p.id == product_id), None)
            if product:
                self.product_desc_display.setText(product.reference)
        else:
            self.product_desc_display.clear()
    
    def populate_fields(self):
        """Populate form fields with existing order data."""
        if self.order:
            self.po_reference_input.setText(self.order.po_reference)
            
            # Select the product in combo box
            for i in range(self.product_combo.count()):
                if self.product_combo.itemData(i) == self.order.product_id:
                    self.product_combo.setCurrentIndex(i)
                    break
            
            self.quantity_input.setValue(self.order.quantity)
            
            if self.order.warehouse_location:
                self.warehouse_input.setText(self.order.warehouse_location)
            
            # Update stock info
            used = self.order.quantity - self.order.remaining_stock
            self.stock_info_label.setText(
                f"📊 Stock Status: {self.order.remaining_stock} remaining "
                f"({used} used, {self.order.quantity} total)"
            )
            
            # Disable product and quantity changes if stock has been used
            if used > 0:
                self.product_combo.setEnabled(False)
                self.quantity_input.setEnabled(False)
                QMessageBox.information(
                    self,
                    "Limited Editing",
                    "Product and quantity cannot be changed because stock has been used.\n"
                    "You can only update PO reference and warehouse location."
                )
    
    def validate_input(self) -> tuple[bool, str]:
        """
        Validate user input using centralized validators.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Sanitize input
        po_reference = sanitize_input(self.po_reference_input.text())
        product_id = self.product_combo.currentData()
        quantity = self.quantity_input.value()
        
        # Validate PO reference
        is_valid, error_msg = validate_po_reference(po_reference)
        if not is_valid:
            return False, f"PO reference error: {error_msg}"
        
        # Validate product selection
        if not product_id:
            return False, "Please select a product."
        
        # Validate quantity
        is_valid, error_msg = validate_quantity(quantity)
        if not is_valid:
            return False, f"Quantity error: {error_msg}"
        
        # Normalize reference
        po_reference_normalized = normalize_reference(po_reference)
        
        # Check for duplicate PO reference
        if not self.is_edit_mode or (self.order and po_reference_normalized != self.order.po_reference):
            if self.is_po_reference_duplicate(po_reference_normalized):
                return False, f"PO reference '{po_reference_normalized}' already exists. Please use a unique reference."
        
        return True, ""
    
    def is_po_reference_duplicate(self, po_reference: str) -> bool:
        """Check if PO reference already exists in database."""
        try:
            with self.db_manager.get_session() as session:
                existing = session.query(PurchaseOrder).filter(
                    PurchaseOrder.po_reference == po_reference.upper()
                ).first()
                return existing is not None
        except Exception:
            return False
    
    def save_order(self):
        """Save the purchase order to database."""
        # Validate input
        is_valid, error_msg = self.validate_input()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        try:
            # Sanitize and normalize inputs
            po_reference = normalize_reference(sanitize_input(self.po_reference_input.text()))
            product_id = self.product_combo.currentData()
            quantity = self.quantity_input.value()
            warehouse = sanitize_input(self.warehouse_input.text())
            
            if self.is_edit_mode:
                # Update existing order
                self.order.po_reference = po_reference
                self.order.warehouse_location = warehouse if warehouse else None
                
                # Only update product and quantity if no stock has been used
                if self.order.remaining_stock == self.order.quantity:
                    self.order.product_id = product_id
                    self.order.quantity = quantity
                    self.order.remaining_stock = quantity
                
                self.db_manager.update(self.order)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Purchase order '{po_reference}' updated successfully!"
                )
            else:
                # Create new order
                new_order = PurchaseOrder(
                    po_reference=po_reference,
                    product_id=product_id,
                    quantity=quantity,
                    remaining_stock=quantity,  # Initially, remaining = quantity
                    warehouse_location=warehouse if warehouse else None
                )
                self.db_manager.add(new_order)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Purchase order '{po_reference}' added successfully!\n"
                    f"Initial stock: {quantity} units"
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Order",
                f"Failed to save purchase order:\n{str(e)}"
            )
