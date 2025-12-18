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
    QDoubleSpinBox,
    QComboBox,
    QPushButton,
    QLabel,
    QMessageBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt
from decimal import Decimal

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
        self.quantity_input.valueChanged.connect(self.calculate_totals)
        form_layout.addRow("Quantity: *", self.quantity_input)

        # --- Make unit price keyboard friendly ---
        # After quantity, focus should go to unit price
        # We'll set tab order after all widgets are created
        
        # Warehouse Location
        self.warehouse_input = QLineEdit()
        self.warehouse_input.setPlaceholderText("Enter warehouse location (optional)")
        form_layout.addRow("Warehouse:", self.warehouse_input)
        
        layout.addLayout(form_layout)
        
        # Pricing Section (Optional)
        pricing_group = QGroupBox("💰 Pricing Information (Optional)")
        pricing_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        pricing_layout = QFormLayout()
        
        # Unit Price
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setRange(0.000, 999999.999)
        self.unit_price_input.setDecimals(3)
        self.unit_price_input.setValue(0.000)
        self.unit_price_input.setSuffix(" BHD")
        self.unit_price_input.valueChanged.connect(self.calculate_totals)
        # Clear field on focus for immediate typing
        self.unit_price_input.lineEdit().installEventFilter(self)
        pricing_layout.addRow("Unit Price:", self.unit_price_input)
        
        # Tax Rate
        self.tax_rate_input = QDoubleSpinBox()
        self.tax_rate_input.setRange(0.00, 100.00)
        self.tax_rate_input.setDecimals(2)
        self.tax_rate_input.setValue(0.00)
        self.tax_rate_input.setSuffix(" %")
        self.tax_rate_input.valueChanged.connect(self.calculate_totals)
        pricing_layout.addRow("Tax Rate:", self.tax_rate_input)
        
        # Calculated fields (read-only)
        self.total_without_tax_display = QLineEdit()
        self.total_without_tax_display.setReadOnly(True)
        self.total_without_tax_display.setStyleSheet("background-color: #f0f0f0; font-weight: bold;")
        pricing_layout.addRow("Total (Before Tax):", self.total_without_tax_display)
        
        self.tax_amount_display = QLineEdit()
        self.tax_amount_display.setReadOnly(True)
        self.tax_amount_display.setStyleSheet("background-color: #f0f0f0;")
        pricing_layout.addRow("Tax Amount:", self.tax_amount_display)
        
        self.total_with_tax_display = QLineEdit()
        self.total_with_tax_display.setReadOnly(True)
        self.total_with_tax_display.setStyleSheet("background-color: #e8f5e9; font-weight: bold; color: #2e7d32;")
        pricing_layout.addRow("Total (With Tax):", self.total_with_tax_display)
        
        pricing_group.setLayout(pricing_layout)
        layout.addWidget(pricing_group)
        
        # Note about optional pricing
        pricing_note = QLabel("💡 Pricing information is optional and can be added later")
        pricing_note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic; margin-top: 5px;")
        layout.addWidget(pricing_note)
        
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
        
        # Set tab order: after quantity, go to unit price
        self.setTabOrder(self.quantity_input, self.unit_price_input)
    
    def eventFilter(self, obj, event):
        """Clear unit price field on focus so user can immediately type."""
        if obj == self.unit_price_input.lineEdit():
            from PyQt6.QtCore import QEvent
            if event.type() == QEvent.Type.FocusIn:
                # Completely clear the field when focused for immediate typing
                if self.unit_price_input.value() == 0.000:
                    # Use QTimer to clear after focus is established
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self.unit_price_input.lineEdit().clear())
                else:
                    # If there's a value, select all for replacement
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self.unit_price_input.lineEdit().selectAll())
        return super().eventFilter(obj, event)
    
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
    
    def calculate_totals(self):
        """Calculate pricing totals based on quantity, unit price, and tax rate."""
        try:
            quantity = self.quantity_input.value()
            unit_price = self.unit_price_input.value()
            tax_rate = self.tax_rate_input.value()
            
            # Calculate total without tax
            total_without_tax = quantity * unit_price
            
            # Calculate tax amount
            tax_amount = total_without_tax * (tax_rate / 100.0)
            
            # Calculate total with tax
            total_with_tax = total_without_tax + tax_amount
            
            # Update display fields
            if unit_price > 0:
                self.total_without_tax_display.setText(f"{total_without_tax:.3f} BHD")
                self.tax_amount_display.setText(f"{tax_amount:.3f} BHD")
                self.total_with_tax_display.setText(f"{total_with_tax:.3f} BHD")
            else:
                self.total_without_tax_display.setText("0.000 BHD")
                self.tax_amount_display.setText("0.000 BHD")
                self.total_with_tax_display.setText("0.000 BHD")
                
        except Exception as e:
            # Silently handle calculation errors
            pass
    
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
            
            # Populate pricing fields if available
            if self.order.unit_price is not None:
                self.unit_price_input.setValue(float(self.order.unit_price))
            
            if self.order.tax_rate is not None:
                self.tax_rate_input.setValue(float(self.order.tax_rate))
            
            # Calculate totals will auto-populate the calculated fields
            self.calculate_totals()
            
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
                    "You can only update PO reference, warehouse location, and pricing information."
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
            
            # Get pricing values (optional)
            unit_price = self.unit_price_input.value() if self.unit_price_input.value() > 0 else None
            tax_rate = self.tax_rate_input.value() if self.tax_rate_input.value() > 0 else None
            
            # Calculate pricing fields
            tax_amount = None
            total_without_tax = None
            total_with_tax = None
            
            if unit_price is not None:
                total_without_tax = quantity * unit_price
                if tax_rate is not None:
                    tax_amount = total_without_tax * (tax_rate / 100.0)
                    total_with_tax = total_without_tax + tax_amount
                else:
                    total_with_tax = total_without_tax
            
            if self.is_edit_mode:
                # Update existing order
                self.order.po_reference = po_reference
                self.order.warehouse_location = warehouse if warehouse else None
                
                # Update pricing information
                self.order.unit_price = unit_price
                self.order.tax_rate = tax_rate
                self.order.tax_amount = tax_amount
                self.order.total_without_tax = total_without_tax
                self.order.total_with_tax = total_with_tax
                
                # Only update product and quantity if no stock has been used
                if self.order.remaining_stock == self.order.quantity:
                    self.order.product_id = product_id
                    self.order.quantity = quantity
                    self.order.remaining_stock = quantity
                    # Recalculate totals if quantity changed
                    if unit_price is not None:
                        total_without_tax = quantity * unit_price
                        if tax_rate is not None:
                            tax_amount = total_without_tax * (tax_rate / 100.0)
                            total_with_tax = total_without_tax + tax_amount
                        else:
                            total_with_tax = total_without_tax
                        self.order.tax_amount = tax_amount
                        self.order.total_without_tax = total_without_tax
                        self.order.total_with_tax = total_with_tax
                
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
                    warehouse_location=warehouse if warehouse else None,
                    unit_price=unit_price,
                    tax_rate=tax_rate,
                    tax_amount=tax_amount,
                    total_without_tax=total_without_tax,
                    total_with_tax=total_with_tax
                )
                self.db_manager.add(new_order)
                
                pricing_info = ""
                if total_with_tax is not None:
                    pricing_info = f"\nTotal cost: {total_with_tax:.3f} BHD"
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Purchase order '{po_reference}' added successfully!\n"
                    f"Initial stock: {quantity} units{pricing_info}"
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Order",
                f"Failed to save purchase order:\n{str(e)}"
            )
