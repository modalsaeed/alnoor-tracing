"""
Products Widget - CRUD interface for product management.

This widget provides a table view of all products with ability to:
- View all products
- Add new products
- Edit existing products
- Delete products
- Search/filter products
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
from PyQt6.QtGui import QIcon

from database import DatabaseManager, Product
from ui.dialogs.product_dialog import ProductDialog


class ProductsWidget(QWidget):
    """Widget for managing products."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.current_products: List[Product] = []
        self.init_ui()
        self.load_products()
    
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
        
        title = QLabel("📦 Products Management")
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
        self.search_input.setPlaceholderText("Search by name or reference...")
        self.search_input.textChanged.connect(self.filter_products)
        self.search_input.setClearButtonEnabled(True)
        layout.addWidget(self.search_input)
        
        return layout
    
    def create_table(self) -> QTableWidget:
        """Create products table."""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['ID', 'Name', 'Reference', 'Description'])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Table settings
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        
        # Double-click to edit
        table.doubleClicked.connect(self.edit_product)
        
        return table
    
    def create_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()
        
        # Add button
        self.add_btn = QPushButton("➕ Add Product")
        self.add_btn.clicked.connect(self.add_product)
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
        self.edit_btn = QPushButton("✏️ Edit Product")
        self.edit_btn.clicked.connect(self.edit_product)
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
        self.delete_btn = QPushButton("🗑️ Delete Product")
        self.delete_btn.clicked.connect(self.delete_product)
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
        self.refresh_btn.clicked.connect(self.load_products)
        layout.addWidget(self.refresh_btn)
        
        # Enable/disable buttons based on selection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        return layout
    
    def load_products(self):
        """Load all products from database."""
        try:
            self.current_products = self.db_manager.get_all(Product)
            self.populate_table(self.current_products)
            self.update_count_label()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Products",
                f"Failed to load products from database:\n{str(e)}"
            )
    
    def populate_table(self, products: List[Product]):
        """Populate table with products."""
        self.table.setSortingEnabled(False)  # Disable sorting while populating
        self.table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # ID
            id_item = QTableWidgetItem(str(product.id))
            id_item.setData(Qt.ItemDataRole.UserRole, product)  # Store product object
            self.table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(product.name)
            self.table.setItem(row, 1, name_item)
            
            # Reference
            ref_item = QTableWidgetItem(product.reference)
            self.table.setItem(row, 2, ref_item)
            
            # Description
            desc = product.description or ""
            desc_item = QTableWidgetItem(desc)
            self.table.setItem(row, 3, desc_item)
        
        self.table.setSortingEnabled(True)  # Re-enable sorting
    
    def filter_products(self):
        """Filter products based on search text."""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            # Show all products
            self.populate_table(self.current_products)
        else:
            # Filter products
            filtered = [
                p for p in self.current_products
                if search_text in p.name.lower() or
                   search_text in p.reference.lower() or
                   (p.description and search_text in p.description.lower())
            ]
            self.populate_table(filtered)
    
    def update_count_label(self):
        """Update the count label."""
        total = len(self.current_products)
        self.count_label.setText(f"Total: {total}")
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def get_selected_product(self) -> Optional[Product]:
        """Get the currently selected product."""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return None
        
        # Get product from first column's UserRole data
        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        return id_item.data(Qt.ItemDataRole.UserRole)
    
    def add_product(self):
        """Open dialog to add new product."""
        dialog = ProductDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_products()  # Reload table after adding
    
    def edit_product(self):
        """Open dialog to edit selected product."""
        product = self.get_selected_product()
        if not product:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a product to edit."
            )
            return
        
        dialog = ProductDialog(self.db_manager, product=product, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_products()  # Reload table after editing
    
    def delete_product(self):
        """Delete selected product."""
        product = self.get_selected_product()
        if not product:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a product to delete."
            )
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete:\n\n"
            f"Name: {product.name}\n"
            f"Reference: {product.reference}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.delete(Product, product.id)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Product '{product.name}' deleted successfully."
                )
                self.load_products()  # Reload table
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Deleting Product",
                    f"Failed to delete product:\n{str(e)}"
                )
