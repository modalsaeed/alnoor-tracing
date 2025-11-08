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

from database import DatabaseManager, DistributionLocation


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
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            'ID', 'Name', 'Reference', 'Address', 'Contact Person', 'Phone'
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
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
            id_item = QTableWidgetItem(str(location.id))
            id_item.setData(Qt.ItemDataRole.UserRole, location)
            self.table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(location.name)
            self.table.setItem(row, 1, name_item)
            
            # Reference
            ref_item = QTableWidgetItem(location.reference)
            self.table.setItem(row, 2, ref_item)
            
            # Address
            address = location.address or ""
            address_item = QTableWidgetItem(address)
            self.table.setItem(row, 3, address_item)
            
            # Contact Person
            contact = location.contact_person or ""
            contact_item = QTableWidgetItem(contact)
            self.table.setItem(row, 4, contact_item)
            
            # Phone
            phone = location.phone or ""
            phone_item = QTableWidgetItem(phone)
            self.table.setItem(row, 5, phone_item)
        
        self.table.setSortingEnabled(True)
    
    def filter_locations(self):
        """Filter locations based on search text."""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            self.populate_table(self.current_locations)
        else:
            filtered = [
                loc for loc in self.current_locations
                if search_text in loc.name.lower() or
                   search_text in loc.reference.lower() or
                   (loc.address and search_text in loc.address.lower()) or
                   (loc.contact_person and search_text in loc.contact_person.lower()) or
                   (loc.phone and search_text in loc.phone.lower())
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
        """Get the currently selected distribution location."""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        return id_item.data(Qt.ItemDataRole.UserRole)
    
    def add_location(self):
        """Open dialog to add new distribution location."""
        from ui.dialogs.distribution_location_dialog import DistributionLocationDialog
        
        dialog = DistributionLocationDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations()
    
    def edit_location(self):
        """Open dialog to edit selected distribution location."""
        location = self.get_selected_location()
        if not location:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a distribution location to edit."
            )
            return
        
        from ui.dialogs.distribution_location_dialog import DistributionLocationDialog
        
        dialog = DistributionLocationDialog(self.db_manager, location=location, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations()
    
    def delete_location(self):
        """Delete selected distribution location."""
        location = self.get_selected_location()
        if not location:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a distribution location to delete."
            )
            return
        
        # Check if location has associated coupons
        with self.db_manager.get_session() as session:
            from database import PatientCoupon
            coupon_count = session.query(PatientCoupon).filter(
                PatientCoupon.distribution_location_id == location.id
            ).count()
        
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
            f"Name: {location.name}\n"
            f"Reference: {location.reference}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.delete(DistributionLocation, location.id)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Distribution location '{location.name}' deleted successfully."
                )
                self.load_locations()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Deleting Location",
                    f"Failed to delete distribution location:\n{str(e)}"
                )
