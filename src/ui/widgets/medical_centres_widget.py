"""
Medical Centres Widget - CRUD interface for medical centre management.

Manages medical centres that issue patient coupons.
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

from src.database.db_manager import DatabaseManager
from src.database.models import MedicalCentre
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class MedicalCentresWidget(QWidget):
    """Widget for managing medical centres."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.current_centres: List[MedicalCentre] = []
        self.init_ui()
        self.load_centres()
    
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
        
        title = QLabel("🏥 Medical Centres Management")
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
        self.search_input.textChanged.connect(self.filter_centres)
        self.search_input.setClearButtonEnabled(True)
        layout.addWidget(self.search_input)
        
        return layout
    
    def create_table(self) -> QTableWidget:
        """Create medical centres table."""
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
        table.doubleClicked.connect(self.edit_centre)
        
        return table
    
    def create_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()
        
        # Add button
        self.add_btn = QPushButton("➕ Add Centre")
        self.add_btn.clicked.connect(self.add_centre)
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
        self.edit_btn = QPushButton("✏️ Edit Centre")
        self.edit_btn.clicked.connect(self.edit_centre)
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
        self.delete_btn = QPushButton("🗑️ Delete Centre")
        self.delete_btn.clicked.connect(self.delete_centre)
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
        self.refresh_btn.clicked.connect(self.load_centres)
        layout.addWidget(self.refresh_btn)
        
        # Enable/disable buttons based on selection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        return layout
    
    def load_centres(self):
        """Load all medical centres from database."""
        try:
            self.current_centres = self.db_manager.get_all(MedicalCentre)
            self.populate_table(self.current_centres)
            self.update_count_label()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Centres",
                f"Failed to load medical centres from database:\n{str(e)}"
            )
    
    def populate_table(self, centres: List[MedicalCentre]):
        """Populate table with medical centres."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(centres))
        
        for row, centre in enumerate(centres):
            # ID
            id_item = QTableWidgetItem(str(get_id(centre)))
            id_item.setData(Qt.ItemDataRole.UserRole, centre)
            self.table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(get_name(centre))
            self.table.setItem(row, 1, name_item)
            
            # Reference
            ref_item = QTableWidgetItem(get_attr(centre, 'reference', ''))
            self.table.setItem(row, 2, ref_item)
            
            # Address
            address = get_attr(centre, 'address', '')
            address_item = QTableWidgetItem(address)
            self.table.setItem(row, 3, address_item)
            
            # Contact Person
            contact = get_attr(centre, 'contact_person', '')
            contact_item = QTableWidgetItem(contact)
            self.table.setItem(row, 4, contact_item)
            
            # Phone
            phone = get_attr(centre, 'phone', '')
            phone_item = QTableWidgetItem(phone)
            self.table.setItem(row, 5, phone_item)
        
        self.table.setSortingEnabled(True)
    
    def filter_centres(self):
        """Filter centres based on search text."""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            self.populate_table(self.current_centres)
        else:
            filtered = [
                centre for centre in self.current_centres
                if search_text in get_name(centre, '').lower() or
                   search_text in get_attr(centre, 'reference', '').lower() or
                   search_text in get_attr(centre, 'address', '').lower() or
                   search_text in get_attr(centre, 'contact_person', '').lower() or
                   search_text in get_attr(centre, 'phone', '').lower()
            ]
            self.populate_table(filtered)
    
    def update_count_label(self):
        """Update the count label."""
        total = len(self.current_centres)
        self.count_label.setText(f"Total: {total}")
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def get_selected_centre(self) -> Optional[MedicalCentre]:
        """Get the currently selected medical centre."""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        return id_item.data(Qt.ItemDataRole.UserRole)
    
    def add_centre(self):
        """Open dialog to add new medical centre."""
        from src.ui.dialogs.medical_centre_dialog import MedicalCentreDialog
        
        dialog = MedicalCentreDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_centres()
    
    def edit_centre(self):
        """Open dialog to edit selected medical centre."""
        centre = self.get_selected_centre()
        if not centre:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a medical centre to edit."
            )
            return
        
        from src.ui.dialogs.medical_centre_dialog import MedicalCentreDialog
        
        dialog = MedicalCentreDialog(self.db_manager, centre=centre, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_centres()
    
    def delete_centre(self):
        """Delete selected medical centre."""
        centre = self.get_selected_centre()
        if not centre:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a medical centre to delete."
            )
            return
        
        # Check if centre has associated coupons
        from src.database.models import PatientCoupon
        all_coupons = self.db_manager.get_all(PatientCoupon)
        coupon_count = sum(1 for c in all_coupons if get_attr(c, 'medical_centre_id') == get_id(centre))
        
        if coupon_count > 0:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                f"This medical centre has {coupon_count} associated coupon(s).\n"
                f"Please reassign or delete those coupons first."
            )
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete:\n\n"
            f"Name: {get_name(centre)}\n"
            f"Reference: {get_attr(centre, 'reference', '')}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.delete(MedicalCentre, get_id(centre))
                QMessageBox.information(
                    self,
                    "Success",
                    f"Medical centre '{get_name(centre)}' deleted successfully."
                )
                self.load_centres()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Deleting Centre",
                    f"Failed to delete medical centre:\n{str(e)}"
                )
