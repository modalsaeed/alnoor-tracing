"""
Purchase Dialog - Add/Edit dialog for supplier purchase management.

Provides a form for creating new purchases from suppliers or editing existing ones.
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
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from decimal import Decimal
from datetime import datetime


from src.database.db_manager import DatabaseManager
from src.database.models import Purchase, PurchaseOrder, Product
from src.utils import sanitize_input
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class PurchaseDialog(QDialog):
    """Dialog for adding or editing a purchase from supplier."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None, purchase: Optional[Purchase] = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.purchase = purchase
        self.is_edit_mode = purchase is not None
        self.purchase_orders = []
        self.products = []
        
        self.init_ui()
        self.load_purchase_orders()
        
        if self.is_edit_mode:
            self.populate_fields()
        else:
            self.calculate_totals()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Edit Purchase" if self.is_edit_mode else "Add New Purchase")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("✏️ Edit Supplier Purchase" if self.is_edit_mode else "➕ Add New Supplier Purchase")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        # Invoice Number
        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("Enter supplier invoice number")
        form_layout.addRow("Invoice Number: *", self.invoice_input)
        
        # Supplier Name
        self.supplier_input = QLineEdit()
        self.supplier_input.setPlaceholderText("Enter supplier name")
        form_layout.addRow("Supplier Name:", self.supplier_input)
        
        # Purchase Date
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Purchase Date: *", self.date_input)
        
        # Local PO Selection
        self.po_combo = QComboBox()
        self.po_combo.currentIndexChanged.connect(self.on_po_changed)
        form_layout.addRow("Local Purchase Order: *", self.po_combo)
        
        # Product (auto-filled based on PO)
        self.product_display = QLineEdit()
        self.product_display.setReadOnly(True)
        self.product_display.setStyleSheet("background-color: #f5f5f5;")
        form_layout.addRow("Product:", self.product_display)
        
        # PO Available Quantity
        self.po_available_display = QLineEdit()
        self.po_available_display.setReadOnly(True)
        self.po_available_display.setStyleSheet("background-color: #fff3cd; font-weight: bold;")
        form_layout.addRow("PO Remaining Qty:", self.po_available_display)
        
        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 100000000)
        self.quantity_input.setValue(1)
        self.quantity_input.setSuffix(" units")
        self.quantity_input.valueChanged.connect(self.calculate_totals)
        self.quantity_input.valueChanged.connect(self.validate_quantity)
        form_layout.addRow("Purchase Quantity: *", self.quantity_input)
        
        # Unit Price
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setRange(0.000001, 999999.99999999)
        self.unit_price_input.setDecimals(6)
        self.unit_price_input.setValue(1.000)
        self.unit_price_input.setSuffix(" BHD")
        self.unit_price_input.valueChanged.connect(self.calculate_totals)
        form_layout.addRow("Unit Price: *", self.unit_price_input)
        
        # Total Price (calculated)
        self.total_price_display = QLineEdit()
        self.total_price_display.setReadOnly(True)
        self.total_price_display.setStyleSheet("background-color: #e8f5e9; font-weight: bold; color: #2e7d32;")
        form_layout.addRow("Total Price:", self.total_price_display)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any additional notes (optional)")
        self.notes_input.setMaximumHeight(80)
        form_layout.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Info box
        info_box = QLabel(
            "ℹ️ <b>About Supplier Purchases:</b><br>"
            "• Select a Local PO from the ministry<br>"
            "• Enter the supplier's invoice details<br>"
            "• Purchase quantity will reduce the PO's remaining stock<br>"
            "• The remaining stock will be available for distribution to locations"
        )
        info_box.setStyleSheet("""
            background-color: #e3f2fd;
            border: 1px solid #90caf9;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
        """)
        info_box.setWordWrap(True)
        layout.addWidget(info_box)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Purchase")
        save_btn.clicked.connect(self.save_purchase)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_purchase_orders(self):
        """Load available purchase orders with remaining stock."""
        try:
            all_pos = sorted(self.db_manager.get_all(PurchaseOrder), key=lambda po: get_attr(po, 'po_reference'))
            if self.is_edit_mode:
                self.purchase_orders = all_pos
                self.po_combo.clear()
                for po in all_pos:
                    display_text = f"{get_attr(po, 'po_reference')} - {get_nested_attr(po, 'product.name')}"
                    self.po_combo.addItem(display_text, get_id(po))
            else:
                self.purchase_orders = [po for po in all_pos if get_attr(po, 'remaining_stock') > 0]
                self.po_combo.clear()
                self.po_combo.addItem("-- Select Local Purchase Order --", None)
                for po in self.purchase_orders:
                    display_text = f"{get_attr(po, 'po_reference')} - {get_nested_attr(po, 'product.name')} ({get_attr(po, 'remaining_stock')} units available)"
                    self.po_combo.addItem(display_text, get_id(po))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load purchase orders: {e}")
    
    def on_po_changed(self, index: int):
        """Handle PO selection change."""
        po_id = self.po_combo.currentData()
        if not po_id:
            self.product_display.clear()
            self.po_available_display.clear()
            return
        
        try:
            po = next((po for po in self.purchase_orders if get_id(po) == po_id), None)
            if po:
                self.product_display.setText(get_nested_attr(po, 'product.name'))
                self.po_available_display.setText(f"{get_attr(po, 'remaining_stock')} units")
                # Set max quantity
                if not self.is_edit_mode:
                    self.quantity_input.setMaximum(get_attr(po, 'remaining_stock'))
                else:
                    max_qty = get_attr(po, 'remaining_stock') + self.purchase.quantity
                    self.quantity_input.setMaximum(max_qty)
        except Exception:
            pass  # Silently fail for UI updates
    
    def validate_quantity(self):
        """Validate that quantity doesn't exceed PO remaining stock."""
        po_id = self.po_combo.currentData()
        if not po_id:
            return
        
        quantity = self.quantity_input.value()
        
        try:
            po = next((po for po in self.purchase_orders if get_id(po) == po_id), None)
            if po:
                max_allowed = get_attr(po, 'remaining_stock')
                if self.is_edit_mode:
                    max_allowed += self.purchase.quantity
                if quantity > max_allowed:
                    self.quantity_input.setStyleSheet("background-color: #ffcccc;")
                else:
                    self.quantity_input.setStyleSheet("")
        except Exception:
            pass  # Silently fail for validation
    
    def calculate_totals(self):
        """Calculate total price."""
        quantity = self.quantity_input.value()
        unit_price = self.unit_price_input.value()
        total = quantity * unit_price
        self.total_price_display.setText(f"{total:.3f} BHD")
    
    def populate_fields(self):
        """Populate fields with existing purchase data."""
        if not self.purchase:
            return
        
        self.invoice_input.setText(self.purchase.invoice_number)
        self.supplier_input.setText(self.purchase.supplier_name or "")
        
        if self.purchase.purchase_date:
            qdate = QDate(
                self.purchase.purchase_date.year,
                self.purchase.purchase_date.month,
                self.purchase.purchase_date.day
            )
            self.date_input.setDate(qdate)
        
        # Set PO
        for i in range(self.po_combo.count()):
            if self.po_combo.itemData(i) == self.purchase.purchase_order_id:
                self.po_combo.setCurrentIndex(i)
                break
        
        self.quantity_input.setValue(self.purchase.quantity)
        self.unit_price_input.setValue(float(self.purchase.unit_price))
        self.notes_input.setPlainText(self.purchase.notes or "")
        
        # Disable PO selection in edit mode (can't change PO)
        self.po_combo.setEnabled(False)
    
    def save_purchase(self):
        """Save the purchase to database."""
        # Validate inputs
        invoice_number = sanitize_input(self.invoice_input.text())
        if not invoice_number:
            QMessageBox.warning(self, "Validation Error", "Invoice number is required.")
            self.invoice_input.setFocus()
            return
        
        po_id = self.po_combo.currentData()
        if not po_id:
            QMessageBox.warning(self, "Validation Error", "Please select a Local Purchase Order.")
            self.po_combo.setFocus()
            return
        
        quantity = self.quantity_input.value()
        if quantity <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0.")
            self.quantity_input.setFocus()
            return
        
        unit_price = self.unit_price_input.value()
        if unit_price <= 0:
            QMessageBox.warning(self, "Validation Error", "Unit price must be greater than 0.")
            self.unit_price_input.setFocus()
            return
        
        try:
            po = next((po for po in self.purchase_orders if get_id(po) == po_id), None)
            if not po:
                QMessageBox.critical(self, "Error", "Selected purchase order not found.")
                return
            # Validate quantity against PO remaining stock
            if not self.is_edit_mode:
                if quantity > get_attr(po, 'remaining_stock'):
                    QMessageBox.warning(
                        self,
                        "Insufficient Stock",
                        f"Purchase quantity ({quantity}) exceeds PO remaining stock ({get_attr(po, 'remaining_stock')})."
                    )
                    return
            else:
                available = get_attr(po, 'remaining_stock') + self.purchase.quantity
                if quantity > available:
                    QMessageBox.warning(
                        self,
                        "Insufficient Stock",
                        f"Purchase quantity ({quantity}) exceeds available stock ({available})."
                    )
                    return
            # Check for duplicate invoice number
            all_purchases = self.db_manager.get_all(Purchase)
            if not self.is_edit_mode:
                existing = next((p for p in all_purchases if get_attr(p, 'invoice_number') == invoice_number), None)
                if existing:
                    QMessageBox.warning(
                        self,
                        "Duplicate Invoice",
                        f"Invoice number '{invoice_number}' already exists."
                    )
                    return
            else:
                if invoice_number != self.purchase.invoice_number:
                    existing = next((p for p in all_purchases if get_attr(p, 'invoice_number') == invoice_number), None)
                    if existing:
                        QMessageBox.warning(
                            self,
                            "Duplicate Invoice",
                            f"Invoice number '{invoice_number}' already exists."
                        )
                        return
            # Get date
            qdate = self.date_input.date()
            purchase_date = datetime(qdate.year(), qdate.month(), qdate.day())
            # Calculate total
            total_price = Decimal(str(quantity * unit_price))
            if self.is_edit_mode:
                # Update existing purchase
                old_quantity = self.purchase.quantity
                quantity_diff = quantity - old_quantity
                self.purchase.invoice_number = invoice_number
                self.purchase.supplier_name = sanitize_input(self.supplier_input.text())
                self.purchase.purchase_date = purchase_date
                self.purchase.quantity = quantity
                self.purchase.remaining_stock = self.purchase.remaining_stock + quantity_diff
                self.purchase.unit_price = Decimal(str(unit_price))
                self.purchase.total_price = total_price
                    self.purchase.notes = sanitize_input(self.notes_input.toPlainText())
                    self.purchase.updated_at = datetime.now()
                    
                    # Adjust PO remaining stock
                    po.remaining_stock -= quantity_diff
                    
                else:
                    # Create new purchase
                    purchase = Purchase(
                        invoice_number=invoice_number,
                        purchase_order_id=po_id,
                        product_id=po.product_id,
                        quantity=quantity,
                        remaining_stock=quantity,  # Initially, all stock is available
                        unit_price=Decimal(str(unit_price)),
                        total_price=total_price,
                        purchase_date=purchase_date,
                        supplier_name=sanitize_input(self.supplier_input.text()),
                        notes=sanitize_input(self.notes_input.toPlainText()),
                    )
                    
                    # Reduce PO remaining stock
                    po.remaining_stock -= quantity
                    
                    session.add(purchase)
                    
                    # Flush to get IDs
                    session.flush()
                    purchase_id = purchase.id
                
            # Context manager will commit here
            QMessageBox.information(
                self,
                "Success",
                f"Purchase {invoice_number} {'updated' if self.is_edit_mode else 'created'} successfully!"
            )
            self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save purchase: {e}")
