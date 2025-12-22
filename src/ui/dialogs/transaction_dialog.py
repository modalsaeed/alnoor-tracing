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
        with self.db_manager.get_session() as session:
            products = session.query(Product).order_by(Product.name).all()
            
            self.product_combo.clear()
            self.product_combo.addItem("-- Select Product --", None)
            for product in products:
                self.product_combo.addItem(
                    f"{product.name} ({product.reference})",
                    product.id
                )
            
            # Load distribution locations
            locations = session.query(DistributionLocation).order_by(DistributionLocation.name).all()
            
            self.location_combo.clear()
            self.location_combo.addItem("-- Select Location --", None)
            for location in locations:
                self.location_combo.addItem(location.name, location.id)
    
    def on_product_changed(self):
        """Handle product selection change."""
        product_id = self.product_combo.currentData()
        
        if product_id is None:
            self.purchase_combo.clear()
            self.purchase_combo.addItem("-- Select Product First --", None)
            self.stock_info_label.setText("Select a product to view stock information")
            return
        
        # Load purchases for this product (only with remaining stock)
        with self.db_manager.get_session() as session:
            purchases = session.query(Purchase).filter(
                Purchase.product_id == product_id,
                Purchase.remaining_stock > 0
            ).order_by(Purchase.purchase_date.desc()).all()
            
            self.purchase_combo.clear()
            self.purchase_combo.addItem("-- Select Supplier Purchase --", None)
            
            for purchase in purchases:
                supplier = purchase.supplier_name or "Unknown Supplier"
                display_text = f"{purchase.invoice_number} - {supplier} - Stock: {purchase.remaining_stock}/{purchase.quantity}"
                self.purchase_combo.addItem(display_text, purchase.id)
        
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
        with self.db_manager.get_session() as session:
            product = session.query(Product).get(product_id)
            
            # Calculate total available stock from all purchases
            total_stock = session.query(Purchase).filter(
                Purchase.product_id == product_id
            ).with_entities(
                Purchase.remaining_stock
            ).all()
            total_available = sum(p[0] for p in total_stock)
            
            info_text = f"<b>{product.name}</b><br><br>"
            info_text += f"<b>Total Available Stock:</b> {total_available} pieces<br>"
            
            # If a specific purchase is selected, show its details
            if purchase_id:
                purchase = session.query(Purchase).get(purchase_id)
                if purchase:
                    info_text += f"<br><b>Selected Supplier Purchase:</b><br>"
                    info_text += f"  Invoice: {purchase.invoice_number}<br>"
                    info_text += f"  Supplier: {purchase.supplier_name or 'N/A'}<br>"
                    info_text += f"  Total Quantity: {purchase.quantity} pieces<br>"
                    info_text += f"  Remaining: {purchase.remaining_stock} pieces<br>"
                    info_text += f"  Purchase Date: {purchase.purchase_date.strftime('%d/%m/%Y')}<br>"
                    info_text += f"  Unit Price: {float(purchase.unit_price):.3f} BHD<br>"
            
            # Show stock status
            if total_available == 0:
                info_text += "<br><span style='color: #dc3545; font-weight: bold;'>⚠️ No stock available</span>"
            elif total_available < 100:
                info_text += f"<br><span style='color: #ffc107; font-weight: bold;'>⚠️ Low stock ({total_available} pieces)</span>"
            else:
                info_text += "<br><span style='color: #28a745; font-weight: bold;'>✅ Stock available</span>"
            
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
        with self.db_manager.get_session() as session:
            purchase = session.query(Purchase).get(purchase_id)
            if purchase and quantity > purchase.remaining_stock:
                return False, f"Quantity ({quantity}) exceeds available stock ({purchase.remaining_stock})"
        
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
        with self.db_manager.get_session() as session:
            product = session.query(Product).get(product_id)
            purchase = session.query(Purchase).get(purchase_id)
            location = session.query(DistributionLocation).get(location_id)
            
            reply = QMessageBox.question(
                self,
                "Confirm Transaction",
                f"Create the following transaction?\n\n"
                f"Reference: {reference}\n"
                f"Product: {product.name}\n"
                f"From Purchase: {purchase.invoice_number} ({purchase.supplier_name or 'N/A'})\n"
                f"To Location: {location.name}\n"
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
            with self.db_manager.get_session() as session:
                # Get purchase and validate stock
                purchase = session.query(Purchase).get(purchase_id)
                if purchase.remaining_stock < quantity:
                    QMessageBox.critical(
                        self,
                        "Insufficient Stock",
                        f"Purchase only has {purchase.remaining_stock} pieces remaining."
                    )
                    return
                
                # Create transaction
                transaction = Transaction(
                    transaction_reference=reference if reference else None,
                    purchase_id=purchase_id,
                    product_id=product_id,
                    distribution_location_id=location_id,
                    quantity=quantity,
                    transaction_date=transaction_date
                )
                
                # Reduce purchase stock
                purchase.remaining_stock -= quantity
                
                session.add(transaction)
                session.commit()
                
                QMessageBox.information(
                    self,
                    "Transaction Created",
                    f"✅ Transaction created successfully!\n\n"
                    f"Transaction Reference: {reference}\n"
                    f"Transaction ID: {transaction.id}\n\n"
                    f"Stock has been updated."
                )
                self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create transaction:\n{str(e)}"
            )

