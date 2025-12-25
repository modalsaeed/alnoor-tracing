"""
Purchases Widget - CRUD interface for supplier purchase management.

Manages purchases made from suppliers based on Local Purchase Orders.
Tracks supplier invoices, quantities, and remaining stock for distribution.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QLabel,
    QMessageBox,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.database.models import Purchase, PurchaseOrder, Product
from src.utils import Colors, Fonts, Spacing, StyleSheets, IconStyles
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class PurchasesWidget(QWidget):
    """Widget for managing supplier purchases."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.current_purchases: List[Purchase] = []
        self.init_ui()
        self.load_purchases()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Header section
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        
        # Search section
        search_layout = self.create_search_bar()
        layout.addLayout(search_layout)
        
        # Table section
        self.table = self.create_table()
        layout.addWidget(self.table)
        
        # Button section
        button_layout = self.create_buttons()
        layout.addLayout(button_layout)
    
    def create_header(self) -> QHBoxLayout:
        """Create header with title and info."""
        layout = QHBoxLayout()
        
        title = QLabel(f"🛒 Supplier Purchases Management")
        title.setStyleSheet(f"""
            font-size: {Fonts.SIZE_LARGE}px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        self.count_label = QLabel("Total: 0")
        self.count_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_NORMAL}px;
            color: {Colors.TEXT_SECONDARY};
        """)
        layout.addWidget(self.count_label)
        
        return layout
    
    def create_search_bar(self) -> QHBoxLayout:
        """Create search/filter bar."""
        layout = QHBoxLayout()
        
        search_label = QLabel(f"{IconStyles.SEARCH} Search:")
        layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by invoice number, supplier, or product...")
        self.search_input.textChanged.connect(self.filter_purchases)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet(StyleSheets.input_field())
        layout.addWidget(self.search_input)
        
        return layout
    
    def create_table(self) -> QTableWidget:
        """Create purchases table."""
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels([
            "ID",
            "Invoice Number",
            "Supplier",
            "Purchase Date",
            "Local PO",
            "Product",
            "Quantity",
            "Remaining",
            "Unit Price",
            "Total Price",
            "Status"
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Invoice
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Supplier
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # PO
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Product
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Qty
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Remaining
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Unit Price
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Total
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Status
        
        table.setColumnWidth(0, 50)  # ID
        
        # Hide ID column
        table.setColumnHidden(0, True)
        
        # Style table
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Double click to view/edit
        table.doubleClicked.connect(self.edit_purchase)
        
        return table
    
    def create_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()
        
        # Add Purchase button
        self.add_btn = QPushButton(f"{IconStyles.ADD} Add Purchase")
        self.add_btn.clicked.connect(self.add_purchase)
        self.add_btn.setStyleSheet(StyleSheets.button_primary())
        layout.addWidget(self.add_btn)
        
        # Edit Purchase button
        self.edit_btn = QPushButton(f"{IconStyles.EDIT} Edit Purchase")
        self.edit_btn.clicked.connect(self.edit_purchase)
        self.edit_btn.setEnabled(False)
        layout.addWidget(self.edit_btn)
        
        # Delete Purchase button
        self.delete_btn = QPushButton(f"{IconStyles.DELETE} Delete Purchase")
        self.delete_btn.clicked.connect(self.delete_purchase)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet(StyleSheets.button_primary(Colors.ERROR))
        layout.addWidget(self.delete_btn)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton(f"{IconStyles.REFRESH} Refresh")
        refresh_btn.clicked.connect(self.load_purchases)
        layout.addWidget(refresh_btn)
        
        # Enable/disable buttons based on selection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        return layout
    
    def load_purchases(self):
        """Load all purchases from database."""
        try:
            self.current_purchases = sorted(
                self.db_manager.get_all(Purchase),
                key=lambda p: p.purchase_date,
                reverse=True
            )
            self.display_purchases(self.current_purchases)
            self.update_count_label()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load purchases: {e}")
    
    def display_purchases(self, purchases: List[Purchase]):
        """Display purchases in table."""
        self.table.setRowCount(0)
        
        for purchase in purchases:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # ID (hidden)
            self.table.setItem(row, 0, QTableWidgetItem(str(get_id(purchase))))
            
            # Invoice Number
            self.table.setItem(row, 1, QTableWidgetItem(get_attr(purchase, 'invoice_number', '')))
            
            # Supplier
            supplier = get_attr(purchase, 'supplier_name', 'N/A')
            self.table.setItem(row, 2, QTableWidgetItem(supplier))
            
            # Purchase Date
            date_str = purchase.purchase_date.strftime("%Y-%m-%d") if purchase.purchase_date else "N/A"
            self.table.setItem(row, 3, QTableWidgetItem(date_str))
            
            # Local PO Reference
            po_ref = get_nested_attr(purchase, 'purchase_order.po_reference', 'N/A')
            self.table.setItem(row, 4, QTableWidgetItem(po_ref))
            
            # Product Name
            product_name = get_nested_attr(purchase, 'product.name', 'N/A')
            self.table.setItem(row, 5, QTableWidgetItem(product_name))
            
            # Quantity
            qty_item = QTableWidgetItem(str(purchase.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, qty_item)
            
            # Remaining Stock
            remaining_item = QTableWidgetItem(str(purchase.remaining_stock))
            remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, remaining_item)
            
            # Unit Price
            unit_price_item = QTableWidgetItem(f"{float(purchase.unit_price):.3f} BHD")
            unit_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 8, unit_price_item)
            
            # Total Price
            total_price_item = QTableWidgetItem(f"{float(purchase.total_price):.3f} BHD")
            total_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 9, total_price_item)
            
            # Status
            status_item = QTableWidgetItem()
            if purchase.remaining_stock == 0:
                status_item.setText("Fully Distributed")
                status_item.setForeground(QColor(Colors.SUCCESS))
            elif purchase.remaining_stock < purchase.quantity:
                status_item.setText("Partially Distributed")
                status_item.setForeground(QColor(Colors.WARNING))
            else:
                status_item.setText("Available")
                status_item.setForeground(QColor(Colors.INFO))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 10, status_item)
    
    def filter_purchases(self, text: str):
        """Filter purchases based on search text."""
        if not text:
            self.display_purchases(self.current_purchases)
            return
        
        text = text.lower()
        filtered = [
            p for p in self.current_purchases
            if text in get_attr(p, 'invoice_number', '').lower()
            or text in get_attr(p, 'supplier_name', '').lower()
            or text in get_nested_attr(p, 'product.name', '').lower()
            or text in get_nested_attr(p, 'purchase_order.po_reference', '').lower()
        ]
        self.display_purchases(filtered)
    
    def update_count_label(self):
        """Update the count label."""
        total = len(self.current_purchases)
        total_value = sum(float(p.total_price) for p in self.current_purchases)
        self.count_label.setText(f"Total: {total} purchases | Value: {total_value:.3f} BHD")
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def get_selected_purchase(self) -> Optional[Purchase]:
        """Get the currently selected purchase."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        purchase_id = int(self.table.item(row, 0).text())
        
        return next((p for p in self.current_purchases if get_id(p) == purchase_id), None)
    
    def add_purchase(self):
        """Open dialog to add a new purchase."""
        from src.ui.dialogs.purchase_dialog import PurchaseDialog
        
        dialog = PurchaseDialog(self.db_manager, self)
        if dialog.exec():
            self.load_purchases()
    
    def edit_purchase(self):
        """Open dialog to edit selected purchase."""
        purchase = self.get_selected_purchase()
        if not purchase:
            QMessageBox.warning(self, "No Selection", "Please select a purchase to edit.")
            return
        
        # Check if purchase has been distributed
        if purchase.remaining_stock < purchase.quantity:
            reply = QMessageBox.question(
                self,
                "Purchase Partially Distributed",
                f"This purchase has been partially distributed ({purchase.quantity - purchase.remaining_stock} units).\n"
                "Editing may affect transaction records. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        from src.ui.dialogs.purchase_dialog import PurchaseDialog
        
        dialog = PurchaseDialog(self.db_manager, self, purchase)
        if dialog.exec():
            self.load_purchases()
    
    def delete_purchase(self):
        """Delete selected purchase."""
        purchase = self.get_selected_purchase()
        if not purchase:
            QMessageBox.warning(self, "No Selection", "Please select a purchase to delete.")
            return
        
        # Check if purchase has been distributed
        if purchase.remaining_stock < purchase.quantity:
            QMessageBox.critical(
                self,
                "Cannot Delete",
                f"This purchase has been distributed to locations ({purchase.quantity - purchase.remaining_stock} units).\n"
                "You cannot delete a purchase that has active transactions."
            )
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete purchase:\n"
            f"Invoice: {get_attr(purchase, 'invoice_number', '')}\n"
            f"Supplier: {get_attr(purchase, 'supplier_name', 'N/A')}\n"
            f"Quantity: {purchase.quantity}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Use db_manager.delete() which works with both local and client mode
            success = self.db_manager.delete(Purchase, get_id(purchase))
            if not success:
                QMessageBox.warning(self, "Error", "Purchase not found.")
                return
            
            QMessageBox.information(self, "Success", "Purchase deleted successfully.")
            self.load_purchases()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete purchase: {e}")
    
    def refresh(self):
        """Refresh the widget data."""
        self.load_purchases()
