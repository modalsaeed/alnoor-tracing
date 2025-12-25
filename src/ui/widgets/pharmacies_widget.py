"""
Pharmacies Widget - Display and manage pharmacies
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional, List

from src.database import Pharmacy
from src.database.db_manager import DatabaseManager
from src.ui.dialogs.pharmacy_dialog import PharmacyDialog
from src.utils import StyleSheets
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class PharmaciesWidget(QWidget):
    """Widget for managing pharmacies."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.current_pharmacies: List[Pharmacy] = []
        self.setup_ui()
        self.load_pharmacies()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Pharmacies")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Count label
        self.count_label = QLabel("Total: 0")
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # Search and actions
        actions_layout = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search pharmacies...")
        self.search_input.textChanged.connect(self.filter_pharmacies)
        self.search_input.setMaximumWidth(300)
        actions_layout.addWidget(self.search_input)
        
        actions_layout.addStretch()
        
        # Action buttons
        self.add_btn = QPushButton("Add Pharmacy")
        self.add_btn.clicked.connect(self.add_pharmacy)
        self.add_btn.setStyleSheet(StyleSheets.button_primary())
        actions_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_pharmacy)
        self.edit_btn.setEnabled(False)
        actions_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_pharmacy)
        self.delete_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_pharmacies)
        actions_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(actions_layout)
        
        # Table
        self.table = self.create_table()
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def create_table(self) -> QTableWidget:
        """Create and configure the pharmacies table."""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(['ID', 'Name', 'Reference', 'Contact Person', 'Phone', 'Email'])
        
        # Set column properties
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Reference
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Contact Person
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Phone
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Email
        
        # Enable sorting
        table.setSortingEnabled(True)
        
        # Selection behavior
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Double-click to edit
        table.doubleClicked.connect(self.edit_pharmacy)
        
        return table
    
    def load_pharmacies(self):
        """Load all pharmacies from the database."""
        try:
            # Use get_all() which works with both DatabaseManager and DatabaseClient
            pharmacies = self.db_manager.get_all(Pharmacy)
            self.current_pharmacies = pharmacies
            
            self.populate_table(self.current_pharmacies)
            self.update_count_label()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load pharmacies: {str(e)}")
    
    def populate_table(self, pharmacies: List[Pharmacy]):
        """Populate the table with pharmacies."""
        self.table.setSortingEnabled(False)  # Disable sorting during population
        self.table.setRowCount(0)
        
        for row, pharmacy in enumerate(pharmacies):
            self.table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(get_id(pharmacy)))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(get_name(pharmacy))
            self.table.setItem(row, 1, name_item)
            
            # Reference
            ref_item = QTableWidgetItem(get_attr(pharmacy, 'reference', ''))
            self.table.setItem(row, 2, ref_item)
            
            # Contact Person
            contact = get_attr(pharmacy, 'contact_person', '')
            contact_item = QTableWidgetItem(contact)
            self.table.setItem(row, 3, contact_item)
            
            # Phone
            phone = get_attr(pharmacy, 'phone', '')
            phone_item = QTableWidgetItem(phone)
            self.table.setItem(row, 4, phone_item)
            
            # Email
            email = get_attr(pharmacy, 'email', '')
            email_item = QTableWidgetItem(email)
            self.table.setItem(row, 5, email_item)
        
        self.table.setSortingEnabled(True)  # Re-enable sorting
    
    def filter_pharmacies(self):
        """Filter pharmacies based on search text."""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            # Show all pharmacies
            self.populate_table(self.current_pharmacies)
        else:
            # Filter pharmacies
            filtered = [
                p for p in self.current_pharmacies
                if search_text in get_name(p, '').lower() or
                   search_text in get_attr(p, 'reference', '').lower() or
                   search_text in get_attr(p, 'contact_person', '').lower() or
                   search_text in get_attr(p, 'phone', '').lower() or
                   search_text in get_attr(p, 'email', '').lower()
            ]
            self.populate_table(filtered)
    
    def update_count_label(self):
        """Update the count label."""
        total = len(self.current_pharmacies)
        self.count_label.setText(f"Total: {total}")
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def get_selected_pharmacy(self) -> Optional[Pharmacy]:
        """Get the currently selected pharmacy."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return None
        
        pharmacy_id = int(self.table.item(selected_row, 0).text())
        
        # Find the pharmacy in current list
        for pharmacy in self.current_pharmacies:
            if get_id(pharmacy) == pharmacy_id:
                return pharmacy
        
        return None
    
    def add_pharmacy(self):
        """Show dialog to add a new pharmacy."""
        dialog = PharmacyDialog(self.db_manager, parent=self)
        dialog.pharmacy_saved.connect(self.load_pharmacies)
        dialog.exec()
    
    def edit_pharmacy(self):
        """Show dialog to edit the selected pharmacy."""
        pharmacy = self.get_selected_pharmacy()
        if not pharmacy:
            return
        
        dialog = PharmacyDialog(self.db_manager, pharmacy, parent=self)
        dialog.pharmacy_saved.connect(self.load_pharmacies)
        dialog.exec()
    
    def delete_pharmacy(self):
        """Delete the selected pharmacy."""
        pharmacy = self.get_selected_pharmacy()
        if not pharmacy:
            return
        
        # Check if pharmacy has distribution locations
        try:
            with self.db_manager.get_session() as session:
                pharmacy = session.merge(pharmacy)
                location_count = len(pharmacy.distribution_locations)
                
                if location_count > 0:
                    result = QMessageBox.warning(
                        self, "Warning",
                        f"This pharmacy has {location_count} distribution location(s).\n"
                        f"Deleting this pharmacy will also delete all associated locations.\n\n"
                        f"Are you sure you want to continue?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if result != QMessageBox.StandardButton.Yes:
                        return
                else:
                    result = QMessageBox.question(
                        self, "Confirm Delete",
                        f"Are you sure you want to delete the pharmacy '{get_name(pharmacy)}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if result != QMessageBox.StandardButton.Yes:
                        return
                
                # Delete the pharmacy
                session.delete(pharmacy)
                session.commit()
                
                QMessageBox.information(self, "Success", "Pharmacy deleted successfully.")
                self.load_pharmacies()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete pharmacy: {str(e)}")
