"""
Transaction Dialog - Create and view product transfer transactions.

Allows users to record when products are transferred from purchase orders
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
from src.database.models import Product, PurchaseOrder, DistributionLocation
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
            "ℹ️ Record a product transfer from a purchase order to a distribution location.\n"
            "Stock will be deducted automatically using FIFO (First In, First Out) method."
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
        self.reference_input.setPlaceholderText("e.g., TRX-2024-001")
        self.reference_input.setMaxLength(100)
        form_layout.addRow("Transaction Reference: *", self.reference_input)
        
        # Product Selection
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        form_layout.addRow("Product: *", self.product_combo)
        
        # Purchase Order Selection
        self.po_combo = QComboBox()
        self.po_combo.currentIndexChanged.connect(self.on_po_changed)
        form_layout.addRow("Purchase Order: *", self.po_combo)
        
        # Distribution Location
        self.location_combo = QComboBox()
        form_layout.addRow("Distribution Location: *", self.location_combo)
        
        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 999999)
        self.quantity_input.setValue(1)
        self.quantity_input.setSuffix(" pieces")
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
            self.po_combo.clear()
            self.po_combo.addItem("-- Select Product First --", None)
            self.stock_info_label.setText("Select a product to view stock information")
            return
        
        # Load purchase orders for this product
        with self.db_manager.get_session() as session:
            pos = session.query(PurchaseOrder).filter(
                PurchaseOrder.product_id == product_id
            ).order_by(PurchaseOrder.created_at.desc()).all()
            
            self.po_combo.clear()
            self.po_combo.addItem("-- Select Purchase Order --", None)
            
            for po in pos:
                display_text = f"{po.po_reference} - Stock: {po.remaining_stock}/{po.quantity}"
                if po.remaining_stock == 0:
                    display_text += " (Empty)"
                self.po_combo.addItem(display_text, po.id)
        
        # Update stock information
        self.update_stock_info(product_id)
    
    def on_po_changed(self):
        """Handle purchase order selection change."""
        po_id = self.po_combo.currentData()
        product_id = self.product_combo.currentData()
        
        if po_id is None or product_id is None:
            return
        
        # Update stock info when PO changes
        self.update_stock_info(product_id, po_id)
    
    def update_stock_info(self, product_id: int, po_id: int = None):
        """Update the stock information display."""
        total_stock = self.stock_service.get_total_stock_by_product(product_id)
        
        with self.db_manager.get_session() as session:
            product = session.query(Product).get(product_id)
            
            info_text = f"<b>{product.name}</b><br><br>"
            info_text += f"<b>Total Available Stock:</b> {total_stock} pieces<br>"
            
            # If a specific PO is selected, show its details
            if po_id:
                po = session.query(PurchaseOrder).get(po_id)
                if po:
                    info_text += f"<br><b>Selected Purchase Order:</b><br>"
                    info_text += f"  Reference: {po.po_reference}<br>"
                    info_text += f"  Total Quantity: {po.quantity} pieces<br>"
                    info_text += f"  Remaining: {po.remaining_stock} pieces<br>"
                    info_text += f"  Created: {po.created_at.strftime('%d/%m/%Y')}<br>"
            
            # Show stock status
            if total_stock == 0:
                info_text += "<br><span style='color: #dc3545; font-weight: bold;'>⚠️ No stock available</span>"
            elif total_stock < 100:
                info_text += f"<br><span style='color: #ffc107; font-weight: bold;'>⚠️ Low stock ({total_stock} pieces)</span>"
            else:
                info_text += "<br><span style='color: #28a745; font-weight: bold;'>✅ Stock available</span>"
            
            self.stock_info_label.setText(info_text)
    
    def validate_input(self) -> tuple[bool, str]:
        """Validate all input fields."""
        # Transaction reference
        reference = self.reference_input.text().strip()
        if not reference:
            return False, "Transaction reference is required"
        
        is_valid, error_msg = validate_reference(reference, min_length=2, max_length=100)
        if not is_valid:
            return False, error_msg
        
        # Product
        product_id = self.product_combo.currentData()
        if product_id is None:
            return False, "Please select a product"
        
        # Purchase Order
        po_id = self.po_combo.currentData()
        if po_id is None:
            return False, "Please select a purchase order"
        
        # Distribution Location
        location_id = self.location_combo.currentData()
        if location_id is None:
            return False, "Please select a distribution location"
        
        # Quantity
        quantity = self.quantity_input.value()
        if quantity <= 0:
            return False, "Quantity must be greater than 0"
        
        # Validate transaction with stock service
        is_valid, error_msg = self.stock_service.validate_transaction(
            product_id=product_id,
            quantity=quantity,
            purchase_order_id=po_id
        )
        
        if not is_valid:
            return False, error_msg
        
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
        po_id = self.po_combo.currentData()
        location_id = self.location_combo.currentData()
        quantity = self.quantity_input.value()
        
        # Convert QDate to datetime
        q_date = self.date_input.date()
        transaction_date = datetime(q_date.year(), q_date.month(), q_date.day())
        
        # Confirm transaction
        with self.db_manager.get_session() as session:
            product = session.query(Product).get(product_id)
            po = session.query(PurchaseOrder).get(po_id)
            location = session.query(DistributionLocation).get(location_id)
            
            reply = QMessageBox.question(
                self,
                "Confirm Transaction",
                f"Create the following transaction?\n\n"
                f"Reference: {reference}\n"
                f"Product: {product.name}\n"
                f"From PO: {po.po_reference}\n"
                f"To Location: {location.name}\n"
                f"Quantity: {quantity} pieces\n"
                f"Date: {transaction_date.strftime('%d/%m/%Y')}\n\n"
                f"Stock will be deducted using FIFO method.\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Create transaction using stock service
        success, message, transaction = self.stock_service.create_transaction(
            transaction_reference=reference,
            purchase_order_id=po_id,
            product_id=product_id,
            distribution_location_id=location_id,
            quantity=quantity,
            transaction_date=transaction_date
        )
        
        if success:
            QMessageBox.information(
                self,
                "Transaction Created",
                f"✅ {message}\n\n"
                f"Transaction Reference: {reference}\n"
                f"Transaction ID: {transaction.id}\n\n"
                f"Stock has been deducted from purchase orders using FIFO."
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Transaction Failed",
                f"❌ Failed to create transaction:\n\n{message}"
            )
