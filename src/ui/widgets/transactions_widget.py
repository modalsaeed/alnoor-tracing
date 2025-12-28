"""
Transactions Widget - View and manage product transfer transactions.

Displays all transactions in a table with filtering and search capabilities.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QComboBox,
    QLineEdit, QDateEdit, QGroupBox, QFormLayout, QDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont


from src.database.db_manager import DatabaseManager
from src.database.models import Transaction, Product, DistributionLocation
from src.services.stock_service import StockService
from src.ui.dialogs.transaction_dialog import TransactionDialog
from src.utils.model_helpers import get_attr, get_nested_attr


class TransactionsWidget(QWidget):
    """Widget for viewing and managing transactions."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.stock_service = StockService(db_manager)
        
        self.init_ui()
        self.load_transactions()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title and actions
        header_layout = QHBoxLayout()
        
        title = QLabel("📦 Stock Transfer Transactions")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add Transaction button
        add_btn = QPushButton("➕ New Transaction")
        add_btn.clicked.connect(self.add_transaction)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        header_layout.addWidget(add_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_transactions)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        layout.addSpacing(10)
        
        # Filters section
        filter_group = QGroupBox("🔍 Filters")
        filter_layout = QFormLayout()
        
        # Product filter
        self.product_filter = QComboBox()
        self.product_filter.addItem("All Products", None)
        filter_layout.addRow("Product:", self.product_filter)
        
        # Location filter
        self.location_filter = QComboBox()
        self.location_filter.addItem("All Locations", None)
        filter_layout.addRow("Location:", self.location_filter)
        
        # Date range
        date_range_layout = QHBoxLayout()
        self.date_from_input = QDateEdit()
        self.date_from_input.setDate(QDate.currentDate().addMonths(-1))
        self.date_from_input.setCalendarPopup(True)
        self.date_from_input.setDisplayFormat("dd/MM/yyyy")
        date_range_layout.addWidget(QLabel("From:"))
        date_range_layout.addWidget(self.date_from_input)
        
        date_range_layout.addWidget(QLabel("To:"))
        self.date_to_input = QDateEdit()
        self.date_to_input.setDate(QDate.currentDate())
        self.date_to_input.setCalendarPopup(True)
        self.date_to_input.setDisplayFormat("dd/MM/yyyy")
        date_range_layout.addWidget(self.date_to_input)
        date_range_layout.addStretch()
        filter_layout.addRow("Date Range:", date_range_layout)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by transaction reference...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addRow("Search:", self.search_input)
        
        # Apply filters button
        apply_filters_btn = QPushButton("Apply Filters")
        apply_filters_btn.clicked.connect(self.apply_filters)
        filter_layout.addRow("", apply_filters_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        layout.addSpacing(10)
        
        # Summary label
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(
            "background-color: #e3f2fd; padding: 10px; border-radius: 4px; "
            "color: #0c5460; border-left: 4px solid #2196f3;"
        )
        layout.addWidget(self.summary_label)
        
        layout.addSpacing(5)
        
        # Transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(7)
        self.transactions_table.setHorizontalHeaderLabels([
            "Transaction Ref", "Product", "Supplier Invoice", 
            "Distribution Location", "Quantity", "Date", "Created At"
        ])
        
        # Set column widths
        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Transaction Ref
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)            # Product
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # PO
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)            # Location
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Quantity
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Created At
        
        self.transactions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.transactions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.transactions_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.transactions_table)
        
        # Load filter data
        self.load_filter_data()
    
    def load_filter_data(self):
        """Load products and locations for filters."""
        # Load products
        products = sorted(self.db_manager.get_all(Product), key=lambda p: get_attr(p, 'name', ''))
        self.product_filter.clear()
        self.product_filter.addItem("All Products", None)
        for product in products:
            self.product_filter.addItem(f"{get_attr(product, 'name', '')} ({get_attr(product, 'reference', '')})", get_attr(product, 'id'))
        
        # Load locations
        locations = sorted(self.db_manager.get_all(DistributionLocation), key=lambda l: get_attr(l, 'name', ''))
        self.location_filter.clear()
        self.location_filter.addItem("All Locations", None)
        for location in locations:
            self.location_filter.addItem(get_attr(location, 'name', ''), get_attr(location, 'id'))
    
    def load_transactions(self):
        """Load all transactions into the table."""
        transactions = self.db_manager.get_all(Transaction)
        # Use get_attr for dict/ORM compatibility
        transactions = sorted(
            transactions,
            key=lambda t: (
                get_attr(t, 'transaction_date', ''),
                get_attr(t, 'created_at', get_attr(t, 'transaction_date', ''))
            ),
            reverse=True
        )
        self.populate_table(transactions)
        self.update_summary(transactions)
    
    def populate_table(self, transactions):
        """Populate the table with transaction data."""
        self.transactions_table.setRowCount(len(transactions))
        
        for row, txn in enumerate(transactions):
            # Transaction Reference
            ref_item = QTableWidgetItem(get_attr(txn, 'transaction_reference', ''))
            ref_item.setFont(QFont("Consolas", 9))
            self.transactions_table.setItem(row, 0, ref_item)

            # Product
            product_name = get_nested_attr(txn, 'product.name', 'Unknown')
            product_item = QTableWidgetItem(product_name)
            self.transactions_table.setItem(row, 1, product_item)

            # Purchase (Supplier Invoice)
            invoice_ref = get_nested_attr(txn, 'purchase.invoice_number', 'Unknown')
            po_item = QTableWidgetItem(invoice_ref)
            po_item.setFont(QFont("Consolas", 9))
            self.transactions_table.setItem(row, 2, po_item)

            # Distribution Location
            location_name = get_nested_attr(txn, 'distribution_location.name', 'Unknown')
            location_item = QTableWidgetItem(location_name)
            self.transactions_table.setItem(row, 3, location_item)

            # Quantity
            qty_item = QTableWidgetItem(f"{get_attr(txn, 'quantity', 0)} pieces")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.transactions_table.setItem(row, 4, qty_item)

            # Transaction Date (dict/ORM safe)
            transaction_date = get_attr(txn, 'transaction_date', None)
            date_str = ''
            if transaction_date:
                try:
                    if isinstance(transaction_date, str):
                        dt = datetime.fromisoformat(transaction_date)
                        date_str = dt.strftime("%d/%m/%Y")
                    else:
                        date_str = transaction_date.strftime("%d/%m/%Y")
                except Exception:
                    date_str = str(transaction_date)
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.transactions_table.setItem(row, 5, date_item)
            
            # Created At (dict/ORM safe)
            created_at = get_attr(txn, 'created_at', None)
            if created_at is None:
                created_at = get_attr(txn, 'transaction_date', None)
            created_str = ''
            if created_at:
                try:
                    # If string, try to parse to datetime
                    if isinstance(created_at, str):
                        dt = datetime.fromisoformat(created_at)
                        created_str = dt.strftime("%d/%m/%Y %H:%M")
                    else:
                        created_str = created_at.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    created_str = str(created_at)
            created_item = QTableWidgetItem(created_str)
            created_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            created_item.setForeground(Qt.GlobalColor.gray)
            self.transactions_table.setItem(row, 6, created_item)
            
            # Store transaction ID in row (dict/ORM safe)
            self.transactions_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, get_attr(txn, 'id'))
    
    def update_summary(self, transactions):
        """Update the summary label."""
        total_count = len(transactions)
        total_quantity = sum(get_attr(txn, 'quantity', 0) for txn in transactions)
        # Count unique products and locations
        unique_products = len(set(get_attr(txn, 'product_id', None) for txn in transactions if get_attr(txn, 'product_id', None)))
        unique_locations = len(set(get_attr(txn, 'distribution_location_id', None) for txn in transactions if get_attr(txn, 'distribution_location_id', None)))
        
        summary_text = (
            f"📊 <b>Summary:</b> "
            f"{total_count} transaction(s) | "
            f"{total_quantity} total pieces transferred | "
            f"{unique_products} product(s) | "
            f"{unique_locations} location(s)"
        )
        
        self.summary_label.setText(summary_text)
    
    def apply_filters(self):
        """Apply filters to the transactions list."""
        # Get all transactions
        all_transactions = self.db_manager.get_all(Transaction)
        
        # Apply product filter
        product_id = self.product_filter.currentData()
        if product_id is not None:
            all_transactions = [t for t in all_transactions if get_attr(t, 'product_id', None) == product_id]

        # Apply location filter
        location_id = self.location_filter.currentData()
        if location_id is not None:
            all_transactions = [t for t in all_transactions if get_attr(t, 'distribution_location_id', None) == location_id]
        
        # Apply date range filter
        date_from = self.date_from_input.date().toPyDate()
        date_to = self.date_to_input.date().toPyDate()
        
        date_from_dt = datetime(date_from.year, date_from.month, date_from.day, 0, 0, 0)
        date_to_dt = datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59)
        
        all_transactions = [
            t for t in all_transactions
            if date_from_dt <= (
                (datetime.fromisoformat(get_attr(t, 'transaction_date')) if isinstance(get_attr(t, 'transaction_date', None), str) else get_attr(t, 'transaction_date', datetime.min))
            ) <= date_to_dt
        ]

        # Apply search filter
        search_text = self.search_input.text().strip().lower()
        if search_text:
            all_transactions = [
                t for t in all_transactions
                if search_text in (get_attr(t, 'transaction_reference', '') or '').lower()
            ]

        # Sort results
        transactions = sorted(
            all_transactions,
            key=lambda t: (
                get_attr(t, 'transaction_date', ''),
                get_attr(t, 'created_at', get_attr(t, 'transaction_date', ''))
            ),
            reverse=True
        )
        self.populate_table(transactions)
        self.update_summary(transactions)
    
    def add_transaction(self):
        """Open dialog to add a new transaction."""
        dialog = TransactionDialog(self.db_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_transactions()  # Refresh the list
            QMessageBox.information(
                self,
                "Transaction Added",
                "The transaction has been successfully added and stock updated."
            )
