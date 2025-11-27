"""
Purchase Orders Widget - CRUD interface for purchase order management.

Manages purchase orders from Ministry of Health with stock tracking.
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
    QDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.database.db_manager import DatabaseManager
from src.database.models import PurchaseOrder, Product
from src.utils import Colors, Fonts, Spacing, StyleSheets, IconStyles


class PurchaseOrdersWidget(QWidget):
    """Widget for managing purchase orders."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.current_orders: List[PurchaseOrder] = []
        self.init_ui()
        self.load_orders()
    
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
        
        title = QLabel(f"{IconStyles.PURCHASE_ORDER} Purchase Orders Management")
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
        self.search_input.setPlaceholderText("Search by PO reference or product...")
        self.search_input.textChanged.connect(self.filter_orders)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet(StyleSheets.input_field())
        layout.addWidget(self.search_input)
        
        return layout
    
    def create_table(self) -> QTableWidget:
        """Create purchase orders table."""
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            'ID', 'PO Reference', 'Product', 'Quantity', 'Remaining', 'Unit Price', 'Tax', 'Total', 'Status'
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        
        # Table settings
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.setStyleSheet(StyleSheets.table())
        
        # Double-click to edit
        table.doubleClicked.connect(self.edit_order)
        
        return table
    
    def create_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()
        
        # Add button
        self.add_btn = QPushButton(f"{IconStyles.ADD} Add Purchase Order")
        self.add_btn.clicked.connect(self.add_order)
        self.add_btn.setStyleSheet(StyleSheets.button_primary(Colors.SUCCESS))
        layout.addWidget(self.add_btn)
        
        # Edit button
        self.edit_btn = QPushButton(f"{IconStyles.EDIT} Edit Order")
        self.edit_btn.clicked.connect(self.edit_order)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet(StyleSheets.button_primary(Colors.PRIMARY))
        layout.addWidget(self.edit_btn)
        
        # Delete button
        self.delete_btn = QPushButton(f"{IconStyles.DELETE} Delete Order")
        self.delete_btn.clicked.connect(self.delete_order)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet(StyleSheets.button_primary(Colors.ERROR))
        layout.addWidget(self.delete_btn)
        
        layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton(f"{IconStyles.REFRESH} Refresh")
        self.refresh_btn.clicked.connect(self.load_orders)
        self.refresh_btn.setStyleSheet(StyleSheets.button_secondary())
        layout.addWidget(self.refresh_btn)
        
        # Enable/disable buttons based on selection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        return layout
    
    def load_orders(self):
        """Load all purchase orders from database."""
        try:
            self.current_orders = self.db_manager.get_all(PurchaseOrder)
            self.populate_table(self.current_orders)
            self.update_count_label()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Orders",
                f"Failed to load purchase orders from database:\n{str(e)}"
            )
    
    def populate_table(self, orders: List[PurchaseOrder]):
        """Populate table with purchase orders."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(orders))
        
        for row, order in enumerate(orders):
            # ID
            id_item = QTableWidgetItem(str(order.id))
            id_item.setData(Qt.ItemDataRole.UserRole, order)
            self.table.setItem(row, 0, id_item)
            
            # PO Reference
            po_ref_item = QTableWidgetItem(order.po_reference)
            self.table.setItem(row, 1, po_ref_item)
            
            # Product name
            product_name = order.product.name if order.product else "Unknown"
            product_item = QTableWidgetItem(product_name)
            self.table.setItem(row, 2, product_item)
            
            # Quantity
            qty_item = QTableWidgetItem(str(order.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, qty_item)
            
            # Remaining Stock
            remaining_item = QTableWidgetItem(str(order.remaining_stock))
            remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Color code based on stock level
            percentage = (order.remaining_stock / order.quantity * 100) if order.quantity > 0 else 0
            if percentage == 0:
                remaining_item.setBackground(QColor(Colors.ERROR))
                remaining_item.setForeground(QColor("white"))
            elif percentage <= 20:
                remaining_item.setBackground(QColor(Colors.WARNING))
                remaining_item.setForeground(QColor("white"))
            elif percentage <= 50:
                remaining_item.setBackground(QColor(Colors.INFO))
                remaining_item.setForeground(QColor("white"))
            
            self.table.setItem(row, 4, remaining_item)
            
            # Unit Price
            if order.unit_price is not None:
                unit_price = f"{float(order.unit_price):.3f}"
                unit_item = QTableWidgetItem(unit_price)
                unit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                unit_item.setToolTip(f"{float(order.unit_price):.3f} BHD per unit")
            else:
                unit_item = QTableWidgetItem("-")
                unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                unit_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            
            self.table.setItem(row, 5, unit_item)
            
            # Tax
            if order.tax_rate is not None and order.tax_amount is not None:
                tax_text = f"{float(order.tax_rate):.1f}%"
                tax_item = QTableWidgetItem(tax_text)
                tax_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tax_item.setToolTip(f"Tax: {float(order.tax_amount):.3f} BHD ({float(order.tax_rate):.1f}%)")
            else:
                tax_item = QTableWidgetItem("-")
                tax_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tax_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            
            self.table.setItem(row, 6, tax_item)
            
            # Total (with tax if available)
            if order.total_with_tax is not None:
                total_cost = f"{float(order.total_with_tax):.3f}"
                total_item = QTableWidgetItem(total_cost)
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                total_item.setForeground(QColor(Colors.SUCCESS))
                tooltip = f"Subtotal: {float(order.total_without_tax):.3f} BHD\n"
                if order.tax_amount:
                    tooltip += f"Tax: {float(order.tax_amount):.3f} BHD\n"
                tooltip += f"Total: {float(order.total_with_tax):.3f} BHD"
                total_item.setToolTip(tooltip)
            else:
                total_item = QTableWidgetItem("-")
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                total_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            
            self.table.setItem(row, 7, total_item)
            
            # Status
            if order.remaining_stock == 0:
                status = "Depleted"
                status_color = QColor(Colors.ERROR)
            elif order.remaining_stock == order.quantity:
                status = "Full"
                status_color = QColor(Colors.SUCCESS)
            else:
                status = "Partial"
                status_color = QColor(Colors.INFO)
            
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setBackground(status_color)
            status_item.setForeground(QColor("white"))
            self.table.setItem(row, 8, status_item)
        
        self.table.setSortingEnabled(True)
    
    def filter_orders(self):
        """Filter orders based on search text."""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            self.populate_table(self.current_orders)
        else:
            filtered = [
                order for order in self.current_orders
                if search_text in order.po_reference.lower() or
                   (order.product and search_text in order.product.name.lower()) or
                   (order.warehouse_location and search_text in order.warehouse_location.lower())
            ]
            self.populate_table(filtered)
    
    def update_count_label(self):
        """Update the count label."""
        total = len(self.current_orders)
        self.count_label.setText(f"Total: {total}")
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def get_selected_order(self) -> Optional[PurchaseOrder]:
        """Get the currently selected purchase order."""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        return id_item.data(Qt.ItemDataRole.UserRole)
    
    def add_order(self):
        """Open dialog to add new purchase order."""
        from src.ui.dialogs.purchase_order_dialog import PurchaseOrderDialog
        
        dialog = PurchaseOrderDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_orders()
    
    def edit_order(self):
        """Open dialog to edit selected purchase order."""
        order = self.get_selected_order()
        if not order:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a purchase order to edit."
            )
            return
        
        from src.ui.dialogs.purchase_order_dialog import PurchaseOrderDialog
        
        dialog = PurchaseOrderDialog(self.db_manager, order=order, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_orders()
    
    def delete_order(self):
        """Delete selected purchase order."""
        order = self.get_selected_order()
        if not order:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a purchase order to delete."
            )
            return
        
        # Check if stock has been used
        if order.remaining_stock < order.quantity:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                f"This purchase order has been partially or fully used.\n"
                f"Original: {order.quantity}, Remaining: {order.remaining_stock}\n\n"
                f"Cannot delete orders with stock movements."
            )
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete:\n\n"
            f"PO Reference: {order.po_reference}\n"
            f"Product: {order.product.name if order.product else 'Unknown'}\n"
            f"Quantity: {order.quantity}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.delete(PurchaseOrder, order.id)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Purchase order '{order.po_reference}' deleted successfully."
                )
                self.load_orders()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Deleting Order",
                    f"Failed to delete purchase order:\n{str(e)}"
                )
