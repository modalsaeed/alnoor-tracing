"""
Transaction Dialog - Create and view product transfer transactions.

Allows users to record when products are transferred from supplier purchases
to distribution locations, which automatically updates stock levels using FIFO.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QLineEdit, QDateEdit,
    QMessageBox, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from src.database.db_manager import DatabaseManager
from src.database.models import Product, Purchase, DistributionLocation
from src.services.stock_service import StockService
from src.utils.validators import validate_reference, sanitize_input
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class TransactionDialog(QDialog):
    """Dialog for creating product transfer transactions."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.stock_service = StockService(db_manager)
        
        self.setWindowTitle("Create Transaction")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📦 Create Stock Transfer Transaction")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Info message
        info = QLabel(
            "ℹ️ Record a product transfer from a supplier purchase to a distribution location.\n"
            "Stock will be deducted automatically from the supplier purchase."
        )
        info.setStyleSheet(
            "background-color: #d1ecf1; padding: 10px; border-radius: 4px; "
            "color: #0c5460; border-left: 4px solid #17a2b8;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addSpacing(15)
        
        # Form section
        form_group = QGroupBox("Transaction Details")
        form_layout = QFormLayout()
        
        # Transaction Reference
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("e.g., TRX-2024-001 (optional)")
        self.reference_input.setMaxLength(100)
        form_layout.addRow("Transaction Reference:", self.reference_input)
        
        # Product Selection
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        form_layout.addRow("Product: *", self.product_combo)
        
        # Supplier Purchase Selection
        self.purchase_combo = QComboBox()
        self.purchase_combo.currentIndexChanged.connect(self.on_purchase_changed)
        form_layout.addRow("Supplier Purchase: *", self.purchase_combo)
        
        # Distribution Location
        self.location_combo = QComboBox()
        form_layout.addRow("Distribution Location: *", self.location_combo)
        
        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 999999)
        self.quantity_input.setValue(1)
        self.quantity_input.setSuffix(" Unit")
        form_layout.addRow("Quantity: *", self.quantity_input)
        
        # Transaction Date
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Transaction Date: *", self.date_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        layout.addSpacing(10)
        
        # Stock Information Section
        self.stock_info_group = QGroupBox("📊 Stock Information")
        stock_info_layout = QVBoxLayout()
        
        self.stock_info_label = QLabel("Select a product to view stock information")
        self.stock_info_label.setWordWrap(True)
        self.stock_info_label.setStyleSheet("padding: 10px;")
        stock_info_layout.addWidget(self.stock_info_label)
        
        self.stock_info_group.setLayout(stock_info_layout)
        layout.addWidget(self.stock_info_group)
        
        layout.addSpacing(15)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("💾 Create Transaction")
        self.save_btn.clicked.connect(self.save_transaction)
        self.save_btn.setMinimumWidth(160)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def load_data(self):
        """Load products, purchase orders, and distribution locations."""
        # Load products
        products = sorted(self.db_manager.get_all(Product), key=lambda x: get_name(x))
        self.product_combo.clear()
        self.product_combo.addItem("-- Select Product --", None)
        for product in products:
            self.product_combo.addItem(
                f"{get_name(product)} ({get_attr(product, 'reference')})",
                get_id(product)
            )
        # Load distribution locations
        locations = sorted(self.db_manager.get_all(DistributionLocation), key=lambda x: get_name(x))
        self.location_combo.clear()
        self.location_combo.addItem("-- Select Location --", None)
        for location in locations:
            self.location_combo.addItem(get_name(location), get_id(location))
    
    def on_product_changed(self):
        """Handle product selection change."""
        product_id = self.product_combo.currentData()
        
        if product_id is None:
            self.purchase_combo.clear()
            self.purchase_combo.addItem("-- Select Product First --", None)
            self.stock_info_label.setText("Select a product to view stock information")
            return
        
        # Load purchases for this product (only with remaining stock)
        purchases = [p for p in self.db_manager.get_all(Purchase) if get_attr(p, 'product_id') == product_id and get_attr(p, 'remaining_stock') > 0]
        purchases = sorted(purchases, key=lambda x: get_attr(x, 'purchase_date'), reverse=True)
        self.purchase_combo.clear()
        self.purchase_combo.addItem("-- Select Supplier Purchase --", None)
        for purchase in purchases:
            supplier = get_attr(purchase, 'supplier_name') or "Unknown Supplier"
            display_text = f"{get_attr(purchase, 'invoice_number')} - {supplier} - Stock: {get_attr(purchase, 'remaining_stock')}/{get_attr(purchase, 'quantity')}"
            self.purchase_combo.addItem(display_text, get_id(purchase))
        
        # Update stock information
        self.update_stock_info(product_id)
    
    def on_purchase_changed(self):
        """Handle purchase selection change."""
        purchase_id = self.purchase_combo.currentData()
        product_id = self.product_combo.currentData()
        
        if purchase_id is None or product_id is None:
            return
        
        # Update stock info when purchase changes
        self.update_stock_info(product_id, purchase_id)
    
    def update_stock_info(self, product_id: int, purchase_id: int = None):
        """Update the stock information display."""
        product = next((p for p in self.db_manager.get_all(Product) if get_id(p) == product_id), None)
        # Calculate total available stock from all purchases
        total_stock = [get_attr(p, 'remaining_stock') for p in self.db_manager.get_all(Purchase) if get_attr(p, 'product_id') == product_id]
        total_available = sum(total_stock)
        info_text = f"<b>{get_name(product)}</b><br><br>"
        info_text += f"<b>Total Available Stock:</b> {total_available} pieces<br>"
        # If a specific purchase is selected, show its details
        if purchase_id:
            purchase = next((p for p in self.db_manager.get_all(Purchase) if get_id(p) == purchase_id), None)
            if purchase:
                info_text += f"<br><b>Selected Supplier Purchase:</b><br>"
                info_text += f"  Invoice: {get_attr(purchase, 'invoice_number')}<br>"
                info_text += f"  Supplier: {get_attr(purchase, 'supplier_name') or 'Unknown'}<br>"
                info_text += f"  Remaining Stock: {get_attr(purchase, 'remaining_stock')}/{get_attr(purchase, 'quantity')}<br>"
                # Add purchase date and unit price if available
                purchase_date = get_attr(purchase, 'purchase_date')
                if purchase_date:
                    try:
                        info_text += f"  Purchase Date: {purchase_date.strftime('%d/%m/%Y')}<br>"
                    except Exception:
                        info_text += f"  Purchase Date: {purchase_date}<br>"
                unit_price = get_attr(purchase, 'unit_price')
                if unit_price is not None:
                    try:
                        info_text += f"  Unit Price: {float(unit_price):.3f} BHD<br>"
                    except Exception:
                        info_text += f"  Unit Price: {unit_price} BHD<br>"
        # Show stock status
        if total_available == 0:
            info_text += "<br><span style='color: #dc3545; font-weight: bold;'>⚠️ No stock available</span>"
        elif total_available < 100:
            info_text += f"<br><span style='color: #ffc107; font-weight: bold;'>⚠️ Low stock ({total_available} pieces)</span>"
        else:
            info_text += "<br><span style='color: #28a745; font-weight: bold;'>✅ Stock available</span>"
        # Update display
        self.stock_info_label.setText(info_text)
    
    def validate_input(self) -> tuple[bool, str]:
        """Validate all input fields."""
        # Transaction reference
        reference = self.reference_input.text().strip()
        
        # Validate reference format if provided (reference is optional)
        if reference:
            is_valid, error_msg = validate_reference(reference, min_length=2, max_length=100)
            if not is_valid:
                return False, error_msg
        
        # Product
        product_id = self.product_combo.currentData()
        if product_id is None:
            return False, "Please select a product"
        
        # Supplier Purchase
        purchase_id = self.purchase_combo.currentData()
        if purchase_id is None:
            return False, "Please select a supplier purchase"
        
        # Distribution Location
        location_id = self.location_combo.currentData()
        if location_id is None:
            return False, "Please select a distribution location"
        
        # Quantity
        quantity = self.quantity_input.value()
        if quantity <= 0:
            return False, "Quantity must be greater than 0"
        
        # Validate quantity against purchase remaining stock
        if hasattr(self.db_manager, 'get_purchase'):
            purchase = self.db_manager.get_purchase(purchase_id)
            remaining_stock = get_attr(purchase, 'remaining_stock', 0)
            if purchase and quantity > remaining_stock:
                return False, f"Quantity ({quantity}) exceeds available stock ({remaining_stock})"
        else:
            with self.db_manager.get_session() as session:
                purchase = session.query(Purchase).get(purchase_id)
                remaining_stock = get_attr(purchase, 'remaining_stock', 0)
                if purchase and quantity > remaining_stock:
                    return False, f"Quantity ({quantity}) exceeds available stock ({remaining_stock})"
        
        return True, ""
    
    def save_transaction(self):
        """Save the transaction."""
        # Validate input
        is_valid, error_msg = self.validate_input()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Get values
        reference = sanitize_input(self.reference_input.text().strip())
        product_id = self.product_combo.currentData()
        purchase_id = self.purchase_combo.currentData()
        location_id = self.location_combo.currentData()
        quantity = self.quantity_input.value()
        
        # Convert QDate to datetime
        q_date = self.date_input.date()
        transaction_date = datetime(q_date.year(), q_date.month(), q_date.day())
        
        # Confirm transaction
        product = next((p for p in self.db_manager.get_all(Product) if get_id(p) == product_id), None)
        purchase = next((p for p in self.db_manager.get_all(Purchase) if get_id(p) == purchase_id), None)
        location = next((l for l in self.db_manager.get_all(DistributionLocation) if get_id(l) == location_id), None)
        reply = QMessageBox.question(
            self,
            "Confirm Transaction",
            f"Create the following transaction?\n\n"
            f"Reference: {reference}\n"
            f"Product: {get_name(product)}\n"
            f"From Purchase: {get_attr(purchase, 'invoice_number')} ({get_attr(purchase, 'supplier_name') or 'N/A'})\n"
            f"To Location: {get_name(location)}\n"
            f"Quantity: {quantity} pieces\n"
            f"Date: {transaction_date.strftime('%d/%m/%Y')}\n\n"
            f"Stock will be deducted from the supplier purchase.\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Create transaction directly (no stock service needed now)
        from src.database.models import Transaction
        
        try:
            purchase = next((p for p in self.db_manager.get_all(Purchase) if get_id(p) == purchase_id), None)
            if not purchase:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Purchase with ID {purchase_id} not found."
                )
                return
            if get_attr(purchase, 'remaining_stock') < quantity:
                QMessageBox.critical(
                    self,
                    "Insufficient Stock",
                    f"Purchase only has {get_attr(purchase, 'remaining_stock')} pieces remaining."
                )
                return
            from src.database.models import Transaction
            if hasattr(self.db_manager, 'create_transaction'):
                # API mode: call create_transaction with all required fields
                try:
                    result = self.db_manager.create_transaction(
                        purchase_id=purchase_id,
                        product_id=product_id,
                        quantity=quantity,
                        distribution_location_id=location_id,
                        transaction_date=transaction_date.isoformat() if hasattr(transaction_date, 'isoformat') else transaction_date,
                        transaction_reference=reference if reference else None,
                        notes=None
                    )
                    transaction_id = result.get('id')
                    # Reduce purchase stock in local cache (if needed)
                    if isinstance(purchase, dict):
                        purchase['remaining_stock'] = get_attr(purchase, 'remaining_stock', 0) - quantity
                    QMessageBox.information(
                        self,
                        "Transaction Created",
                        f"✅ Transaction created successfully!\n\n"
                        f"Transaction Reference: {reference}\n"
                        f"Transaction ID: {transaction_id}\n\n"
                        f"Stock has been updated."
                    )
                    self.accept()
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to create transaction (API):\n{str(e)}\n\nPurchase stock has NOT been deducted."
                    )
            else:
                # Local ORM: create and add transaction
                transaction = Transaction(
                    transaction_reference=reference if reference else None,
                    purchase_id=purchase_id,
                    product_id=product_id,
                    distribution_location_id=location_id,
                    quantity=quantity,
                    transaction_date=transaction_date
                )
                if hasattr(transaction, 'transaction_type'):
                    transaction.transaction_type = 'transfer'
                # Reduce purchase stock (dict/ORM safe)
                if isinstance(purchase, dict):
                    purchase['remaining_stock'] = get_attr(purchase, 'remaining_stock', 0) - quantity
                else:
                    purchase.remaining_stock -= quantity
                self.db_manager.add(transaction)
                self.db_manager.add(purchase)
                transaction_id = get_id(transaction)
                QMessageBox.information(
                    self,
                    "Transaction Created",
                    f"✅ Transaction created successfully!\n\n"
                    f"Transaction Reference: {reference}\n"
                    f"Transaction ID: {transaction_id}\n\n"
                    f"Stock has been updated."
                )
                self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create transaction:\n{str(e)}\n\n"
                f"Purchase stock has NOT been deducted."
            )


