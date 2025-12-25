"""
Distribution Locations Widget - CRUD interface for distribution location management.

Manages distribution points where products are sent.
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
from src.database.models import DistributionLocation, Transaction, Product, PatientCoupon
from sqlalchemy import func
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class DistributionLocationsWidget(QWidget):
    """Widget for managing distribution locations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.current_locations: List[DistributionLocation] = []
        self.init_ui()
        self.load_locations()
    
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
        
        title = QLabel("📍 Distribution Locations Management")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        self.count_label = QLabel("Total: 0")
        self.count_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        layout.addWidget(self.count_label)
        
        return layout
    
    def create_search_bar(self) -> QHBoxLayout:
        """Create search/filter bar."""
        layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Search:")
        layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, reference, or contact...")
        self.search_input.textChanged.connect(self.filter_locations)
        self.search_input.setClearButtonEnabled(True)
        layout.addWidget(self.search_input)
        
        return layout
    
    def create_table(self) -> QTableWidget:
        """Create distribution locations table."""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            'ID', 'Name', 'Reference', 'Address', 'Contact Person', 'Phone', 'Total Stock'
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        # Table settings
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        
        # Double-click to edit
        table.doubleClicked.connect(self.edit_location)
        
        return table
    
    def create_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()
        
        # Add button
        self.add_btn = QPushButton("➕ Add Location")
        self.add_btn.clicked.connect(self.add_location)
        self.add_btn.setStyleSheet("""
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
        layout.addWidget(self.add_btn)
        
        # Edit button
        self.edit_btn = QPushButton("✏️ Edit Location")
        self.edit_btn.clicked.connect(self.edit_location)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        layout.addWidget(self.edit_btn)
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete Location")
        self.delete_btn.clicked.connect(self.delete_location)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        layout.addWidget(self.delete_btn)
        
        layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_locations)
        layout.addWidget(self.refresh_btn)
        
        # Enable/disable buttons based on selection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        return layout
    
    def get_location_stock(self, location_id: int) -> dict:
        """
        Get stock information for a distribution location.
        
        Stock calculation:
        - Stock IN: Sum of all transactions TO this location
        - Stock OUT: Sum of all coupons FROM this location
        - Net Stock: Stock IN - Stock OUT
        
        Args:
            location_id: The distribution location ID
            
        Returns:
            Dictionary with total stock and breakdown by product
        """
        try:
            # Get all transactions and coupons for this location
            all_transactions = self.db_manager.get_all(Transaction)
            all_coupons = self.db_manager.get_all(PatientCoupon)
            all_products = self.db_manager.get_all(Product)
            
            # Filter and aggregate transactions (Stock IN) by product
            product_stock = {}
            for txn in all_transactions:
                if get_attr(txn, 'distribution_location_id') == location_id:
                    product_id = get_attr(txn, 'product_id')
                    if product_id not in product_stock:
                        product = next((p for p in all_products if get_id(p) == product_id), None)
                        product_stock[product_id] = {
                            'name': get_name(product, 'Unknown'),
                            'in': 0,
                            'out': 0
                        }
                    product_stock[product_id]['in'] += get_attr(txn, 'quantity', 0)
            
            # Filter and aggregate coupons (Stock OUT) by product
            for coupon in all_coupons:
                if get_attr(coupon, 'distribution_location_id') == location_id:
                    product_id = get_attr(coupon, 'product_id')
                    if product_id not in product_stock:
                        product = next((p for p in all_products if get_id(p) == product_id), None)
                        product_stock[product_id] = {
                            'name': get_name(product, 'Unknown'),
                            'in': 0,
                            'out': 0
                        }
                    product_stock[product_id]['out'] += get_attr(coupon, 'quantity_pieces', 0)
            
            # Create a dictionary to track stock by product
            stock_by_product = {}
            
            # Process all products
            for product_id, data in product_stock.items():
                stock_by_product[product_id] = {
                    'product_name': data['name'],
                    'stock_in': data['in'],
                    'stock_out': data['out'],
                    'net_stock': data['in'] - data['out']
                }
            
            # Calculate total net stock
            total_stock = sum(p['net_stock'] for p in stock_by_product.values())
            
            # Create products breakdown list
            products_breakdown = [
                {
                    'product_id': product_id,
                    'product_name': data['product_name'],
                    'quantity': data['net_stock'],
                    'stock_in': data['stock_in'],
                    'stock_out': data['stock_out']
                }
                for product_id, data in stock_by_product.items()
            ]
            
            return {
                'total_stock': total_stock,
                'products': products_breakdown
            }
        except Exception as e:
            return {'total_stock': 0, 'products': []}
    
    def load_locations(self):
        """Load all distribution locations from database."""
        try:
            self.current_locations = self.db_manager.get_all(DistributionLocation)
            self.populate_table(self.current_locations)
            self.update_count_label()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Locations",
                f"Failed to load distribution locations from database:\n{str(e)}"
            )
    
    def populate_table(self, locations: List[DistributionLocation]):
        """Populate table with distribution locations."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(locations))
        
        for row, location in enumerate(locations):
            # ID
            id_item = QTableWidgetItem(str(get_id(location)))
            id_item.setData(Qt.ItemDataRole.UserRole, location)
            self.table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(get_name(location))
            self.table.setItem(row, 1, name_item)
            
            # Reference
            ref_item = QTableWidgetItem(get_attr(location, 'reference', ''))
            self.table.setItem(row, 2, ref_item)
            
            # Address
            address = get_attr(location, 'address', '')
            address_item = QTableWidgetItem(address)
            self.table.setItem(row, 3, address_item)
            
            # Contact Person
            contact = get_attr(location, 'contact_person', '')
            contact_item = QTableWidgetItem(contact)
            self.table.setItem(row, 4, contact_item)
            
            # Phone
            phone = get_attr(location, 'phone', '')
            phone_item = QTableWidgetItem(phone)
            self.table.setItem(row, 5, phone_item)
            
            # Total Stock
            stock_info = self.get_location_stock(get_id(location))
            total_stock = stock_info['total_stock']
            stock_item = QTableWidgetItem(f"{total_stock} pieces")
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Add tooltip with product breakdown including IN/OUT
            if stock_info['products']:
                tooltip_lines = ["Stock by Product:\n"]
                for p in stock_info['products']:
                    tooltip_lines.append(
                        f"• {p['product_name']}:\n"
                        f"  ↓ IN (Transactions): {p['stock_in']} pieces\n"
                        f"  ↑ OUT (Coupons): {p['stock_out']} pieces\n"
                        f"  = Net: {p['quantity']} pieces"
                    )
                stock_item.setToolTip("\n".join(tooltip_lines))
            else:
                stock_item.setToolTip("No stock at this location")
            
            # Color code based on stock level
            if total_stock < 0:
                # Negative stock (overdrawn) - Dark red with bold
                stock_item.setForeground(QColor("#8b0000"))  # Dark red
                stock_item.setText(f"⚠️ {total_stock} pieces (OVERDRAWN)")
            elif total_stock == 0:
                stock_item.setForeground(QColor("#dc3545"))  # Red
            elif total_stock < 100:
                stock_item.setForeground(QColor("#ffc107"))  # Yellow
            else:
                stock_item.setForeground(QColor("#28a745"))  # Green
            
            stock_item.setData(Qt.ItemDataRole.UserRole, total_stock)  # For sorting
            self.table.setItem(row, 6, stock_item)
        
        self.table.setSortingEnabled(True)
    
    def filter_locations(self):
        """Filter locations based on search text."""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            self.populate_table(self.current_locations)
        else:
            filtered = [
                loc for loc in self.current_locations
                if search_text in get_name(loc, '').lower() or
                   search_text in get_attr(loc, 'reference', '').lower() or
                   search_text in get_attr(loc, 'address', '').lower() or
                   search_text in get_attr(loc, 'contact_person', '').lower() or
                   search_text in get_attr(loc, 'phone', '').lower()
            ]
            self.populate_table(filtered)
    
    def update_count_label(self):
        """Update the count label."""
        total = len(self.current_locations)
        self.count_label.setText(f"Total: {total}")
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def get_selected_location(self) -> Optional[DistributionLocation]:
        """Get the currently selected distribution location (dict/ORM safe)."""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        # Always return the ID, not the object itself
        location_id = id_item.text()
        # Find the location in self.current_locations by id (works for dict or ORM)
        for loc in self.current_locations:
            if str(get_id(loc)) == location_id:
                return loc
        return None
    
    def add_location(self):
        """Open dialog to add new distribution location."""
        from src.ui.dialogs.distribution_location_dialog import DistributionLocationDialog
        
        dialog = DistributionLocationDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations()
    
    def edit_location(self):
        """Open dialog to edit selected distribution location (dict/ORM safe)."""
        location = self.get_selected_location()
        if not location:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a distribution location to edit."
            )
            return
        from src.ui.dialogs.distribution_location_dialog import DistributionLocationDialog
        dialog = DistributionLocationDialog(self.db_manager, location=location, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations()
    
    def delete_location(self):
        """Delete selected distribution location (dict/ORM safe)."""
        location = self.get_selected_location()
        if not location:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a distribution location to delete."
            )
            return
        # Check if location has associated coupons
        from src.database.models import PatientCoupon
        all_coupons = self.db_manager.get_all(PatientCoupon)
        location_id = get_id(location)
        coupon_count = sum(1 for c in all_coupons if get_attr(c, 'distribution_location_id') == location_id)
        if coupon_count > 0:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                f"This distribution location has {coupon_count} associated coupon(s).\n"
                f"Please reassign or delete those coupons first."
            )
            return
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete:\n\n"
            f"Name: {get_name(location)}\n"
            f"Reference: {get_attr(location, 'reference', '')}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.delete(DistributionLocation, location_id)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Distribution location '{get_name(location)}' deleted successfully."
                )
                self.load_locations()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Deleting Location",
                    f"Failed to delete distribution location:\n{str(e)}"
                )
