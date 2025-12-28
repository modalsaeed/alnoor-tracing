"""
Bulk Coupon Dialog - Batch insert multiple coupons at once.

Allows entering multiple coupon references with shared product, 
medical centre, and distribution location.
"""

from typing import List
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSpinBox,
    QLineEdit,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon, Product, MedicalCentre, DistributionLocation
from src.utils import sanitize_input
from src.utils.model_helpers import get_attr


class BulkCouponDialog(QDialog):
    """Dialog for bulk inserting multiple coupons."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.products = []
        self.medical_centres = []
        self.distribution_locations = []
        self.coupon_entries = []  # List of (reference, quantity, date) tuples
        
        self.init_ui()
        self.load_dropdown_data()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Bulk Add Coupons")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("📦 Bulk Add Coupons")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Select common product, medical centre, and distribution location, "
            "then add multiple coupon references below."
        )
        instructions.setStyleSheet("color: #6c757d; margin-bottom: 15px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Common fields form
        form_layout = QFormLayout()

        # Product Selection
        self.product_combo = QComboBox()
        form_layout.addRow("Product: *", self.product_combo)

        # MOH Health Centre with quick add
        mc_layout = QHBoxLayout()
        self.medical_centre_combo = QComboBox()
        mc_layout.addWidget(self.medical_centre_combo, 1)
        add_centre_btn = QPushButton("➕")
        add_centre_btn.setMaximumWidth(35)
        add_centre_btn.setToolTip("Quick add new MOH health centre")
        add_centre_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_centre_btn.clicked.connect(self.quick_add_medical_centre)
        mc_layout.addWidget(add_centre_btn)
        form_layout.addRow("MOH Health Centre: *", mc_layout)

        # Distribution Location with quick add
        dl_layout = QHBoxLayout()
        self.distribution_location_combo = QComboBox()
        dl_layout.addWidget(self.distribution_location_combo, 1)
        add_location_btn = QPushButton("➕")
        add_location_btn.setMaximumWidth(35)
        add_location_btn.setToolTip("Quick add new distribution location")
        add_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_location_btn.clicked.connect(self.quick_add_distribution_location)
        dl_layout.addWidget(add_location_btn)
        form_layout.addRow("Distribution Location: *", dl_layout)

        layout.addLayout(form_layout)
        
        # Separator
        separator = QLabel()
        separator.setStyleSheet("border-top: 1px solid #dee2e6; margin: 15px 0;")
        layout.addWidget(separator)
        
        # Add coupon entry section
        entry_label = QLabel("Add Coupon Entries:")
        entry_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #495057; margin-top: 10px;")
        layout.addWidget(entry_label)
        
        # Entry input row
        entry_layout = QHBoxLayout()
        
        entry_layout.addWidget(QLabel("Coupon Ref:"))
        self.coupon_ref_input = QLineEdit()
        self.coupon_ref_input.setPlaceholderText("e.g., CPN-001")
        entry_layout.addWidget(self.coupon_ref_input, 2)
        
        entry_layout.addWidget(QLabel("Qty:"))
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(1)
        entry_layout.addWidget(self.quantity_input, 1)
        
        entry_layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        entry_layout.addWidget(self.date_input, 1)
        
        add_entry_btn = QPushButton("➕ Add")
        add_entry_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_entry_btn.clicked.connect(self.add_entry)
        entry_layout.addWidget(add_entry_btn)
        
        layout.addLayout(entry_layout)
        
        # Table to show entries
        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(4)
        self.entries_table.setHorizontalHeaderLabels(['Coupon Reference', 'Quantity (pieces)', 'Date Received', 'Action'])
        
        header = self.entries_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.entries_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.entries_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.entries_table)
        
        # Summary
        self.summary_label = QLabel("Total Coupons: 0 | Total Pieces: 0")
        self.summary_label.setStyleSheet("font-weight: bold; color: #007bff; margin-top: 10px;")
        layout.addWidget(self.summary_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save All Coupons")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        save_btn.clicked.connect(self.save_all)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_dropdown_data(self):
        """Load data for dropdown fields."""
        try:
            # Load products
            self.products = self.db_manager.get_all(Product)
            self.product_combo.clear()
            for product in self.products:
                name = get_attr(product, 'name', 'Unknown')
                reference = get_attr(product, 'reference', '')
                pid = get_attr(product, 'id', None)
                self.product_combo.addItem(f"{name} ({reference})", pid)

            # Load medical centres
            self.medical_centres = self.db_manager.get_all(MedicalCentre)
            self.medical_centre_combo.clear()
            for centre in self.medical_centres:
                name = get_attr(centre, 'name', 'Unknown')
                cid = get_attr(centre, 'id', None)
                self.medical_centre_combo.addItem(name, cid)

            # Load distribution locations
            self.distribution_locations = self.db_manager.get_all(DistributionLocation)
            self.distribution_location_combo.clear()
            for location in self.distribution_locations:
                name = get_attr(location, 'name', 'Unknown')
                lid = get_attr(location, 'id', None)
                self.distribution_location_combo.addItem(name, lid)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Data",
                f"Failed to load dropdown data:\n{str(e)}"
            )
    
    def add_entry(self):
        """Add a coupon entry to the table."""
        coupon_ref = sanitize_input(self.coupon_ref_input.text().strip().upper())
        quantity = self.quantity_input.value()
        selected_date = self.date_input.date()
        date_received = datetime(selected_date.year(), selected_date.month(), selected_date.day())

        # Validation
        if not coupon_ref:
            QMessageBox.warning(self, "Validation Error", "Coupon reference cannot be empty.")
            return

        # Check if already in list
        for ref, _, _ in self.coupon_entries:
            if ref.upper() == coupon_ref.upper():
                QMessageBox.warning(self, "Duplicate", f"Coupon reference '{coupon_ref}' is already in the list.")
                return

        # Add to list
        self.coupon_entries.append((coupon_ref, quantity, date_received))

        # Add to table
        row = self.entries_table.rowCount()
        self.entries_table.insertRow(row)

        # Coupon reference
        ref_item = QTableWidgetItem(coupon_ref)
        self.entries_table.setItem(row, 0, ref_item)

        # Quantity
        qty_item = QTableWidgetItem(f"{quantity} pieces")
        qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.entries_table.setItem(row, 1, qty_item)

        # Date
        date_item = QTableWidgetItem(selected_date.toString("dd/MM/yyyy"))
        date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.entries_table.setItem(row, 2, date_item)

        # Remove button
        remove_btn = QPushButton("🗑️ Remove")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_btn.clicked.connect(lambda checked, r=row: self.remove_entry(r))
        self.entries_table.setCellWidget(row, 3, remove_btn)

        # Clear inputs (do not increment date)
        self.coupon_ref_input.clear()
        self.quantity_input.setValue(1)
        self.coupon_ref_input.setFocus()

        # Update summary
        self.update_summary()

    def quick_add_medical_centre(self):
        """Quick add a new medical centre with full form (matches MedicalCentreDialog)."""
        from src.utils import validate_name, validate_reference, validate_phone, sanitize_input, normalize_reference
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Medical Centre")
        dialog.setMinimumWidth(550)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("➕ Add New Medical Centre")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter medical centre name")
        form_layout.addRow("Name: *", name_input)

        reference_input = QLineEdit()
        reference_input.setPlaceholderText("Enter unique reference (e.g., MC-001)")
        form_layout.addRow("Reference:", reference_input)

        address_input = QLineEdit()
        address_input.setPlaceholderText("Enter address (optional)")
        form_layout.addRow("Address:", address_input)

        contact_input = QLineEdit()
        contact_input.setPlaceholderText("Enter contact person name (optional)")
        form_layout.addRow("Contact Person:", contact_input)

        phone_input = QLineEdit()
        phone_input.setPlaceholderText("Enter phone number (optional)")
        form_layout.addRow("Phone:", phone_input)

        layout.addLayout(form_layout)

        # Required fields note
        note = QLabel("* Required fields")
        note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(note)

        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        def is_reference_duplicate(reference: str) -> bool:
            try:
                all_centres = self.db_manager.get_all(MedicalCentre)
                from src.utils.model_helpers import get_attr
                existing = next((c for c in all_centres if get_attr(c, 'reference') == reference.upper()), None)
                return existing is not None
            except Exception:
                return False

        def save_centre():
            name = sanitize_input(name_input.text().strip())
            reference = sanitize_input(reference_input.text().strip())
            address = sanitize_input(address_input.text().strip()) or None
            contact = sanitize_input(contact_input.text().strip()) or None
            phone = sanitize_input(phone_input.text().strip()) or None

            # Validation
            is_valid, error_msg = validate_name(name, min_length=2, field_name="Medical centre name")
            if not is_valid:
                QMessageBox.warning(dialog, "Validation Error", error_msg)
                return
            if reference:
                is_valid, error_msg = validate_reference(reference, min_length=2)
                if not is_valid:
                    QMessageBox.warning(dialog, "Validation Error", f"Medical centre reference error: {error_msg}")
                    return
            if phone:
                is_valid, error_msg = validate_phone(phone)
                if not is_valid:
                    QMessageBox.warning(dialog, "Validation Error", f"Phone error: {error_msg}")
                    return
            # Normalize reference if provided
            if reference:
                reference_normalized = normalize_reference(reference)
                if is_reference_duplicate(reference_normalized):
                    QMessageBox.warning(dialog, "Validation Error", f"Reference '{reference_normalized}' already exists. Please use a unique reference.")
                    return

            # Save
            try:
                from src.database.models import MedicalCentre
                new_centre = MedicalCentre(
                    name=name,
                    reference=reference.upper() if reference else None,
                    address=address if address else None,
                    contact_person=contact if contact else None,
                    phone=phone if phone else None
                )
                self.db_manager.add(new_centre)
                QMessageBox.information(dialog, "Success", f"Medical centre '{name}' added successfully!")
                dialog.accept()
                self.load_dropdown_data()  # Refresh dropdowns
            except Exception as e:
                QMessageBox.critical(dialog, "Error Saving Centre", f"Failed to save medical centre:\n{str(e)}")

        save_btn.clicked.connect(save_centre)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def quick_add_distribution_location(self):
        """Quick add a new distribution location with full form (matches DistributionLocationDialog)."""
        from src.utils import validate_name, validate_reference, validate_phone, sanitize_input, normalize_reference
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Distribution Location")
        dialog.setMinimumWidth(550)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("➕ Add New Distribution Location")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter location name")
        form_layout.addRow("Name: *", name_input)

        reference_input = QLineEdit()
        reference_input.setPlaceholderText("Enter unique reference (e.g., LOC-001)")
        form_layout.addRow("Reference:", reference_input)

        trn_input = QLineEdit()
        trn_input.setPlaceholderText("Enter Tax Registration Number")
        trn_input.setMaxLength(100)
        form_layout.addRow("TRN:", trn_input)

        address_input = QLineEdit()
        address_input.setPlaceholderText("Enter address (optional)")
        form_layout.addRow("Address:", address_input)

        contact_input = QLineEdit()
        contact_input.setPlaceholderText("Enter contact person name (optional)")
        form_layout.addRow("Contact Person:", contact_input)

        phone_input = QLineEdit()
        phone_input.setPlaceholderText("Enter phone number (optional)")
        form_layout.addRow("Phone:", phone_input)

        layout.addLayout(form_layout)

        # Required fields note
        note = QLabel("* Required fields")
        note.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(note)

        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        def is_reference_duplicate(reference: str) -> bool:
            try:
                all_locations = self.db_manager.get_all(DistributionLocation)
                from src.utils.model_helpers import get_attr
                existing = next((l for l in all_locations if get_attr(l, 'reference') == reference.upper()), None)
                return existing is not None
            except Exception:
                return False

        def save_location():
            name = sanitize_input(name_input.text().strip())
            reference = sanitize_input(reference_input.text().strip())
            trn = sanitize_input(trn_input.text().strip()) or None
            address = sanitize_input(address_input.text().strip()) or None
            contact = sanitize_input(contact_input.text().strip()) or None
            phone = sanitize_input(phone_input.text().strip()) or None

            # Validation
            is_valid, error_msg = validate_name(name, min_length=2, field_name="Location name")
            if not is_valid:
                QMessageBox.warning(dialog, "Validation Error", error_msg)
                return
            if reference:
                is_valid, error_msg = validate_reference(reference, min_length=2)
                if not is_valid:
                    QMessageBox.warning(dialog, "Validation Error", f"Location reference error: {error_msg}")
                    return
            if phone:
                is_valid, error_msg = validate_phone(phone)
                if not is_valid:
                    QMessageBox.warning(dialog, "Validation Error", f"Phone error: {error_msg}")
                    return
            # Normalize reference if provided
            if reference:
                reference_normalized = normalize_reference(reference)
                if is_reference_duplicate(reference_normalized):
                    QMessageBox.warning(dialog, "Validation Error", f"Reference '{reference_normalized}' already exists. Please use a unique reference.")
                    return

            # Save
            try:
                from src.database.models import DistributionLocation
                new_location = DistributionLocation(
                    name=name,
                    reference=reference.upper() if reference else None,
                    trn=trn if trn else None,
                    address=address if address else None,
                    contact_person=contact if contact else None,
                    phone=phone if phone else None,
                    pharmacy_id=None  # No pharmacy selection in quick add
                )
                self.db_manager.add(new_location)
                QMessageBox.information(dialog, "Success", f"Distribution location '{name}' added successfully!")
                dialog.accept()
                self.load_dropdown_data()  # Refresh dropdowns
            except Exception as e:
                QMessageBox.critical(dialog, "Error Saving Location", f"Failed to save distribution location:\n{str(e)}")

        save_btn.clicked.connect(save_location)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()
    
    def remove_entry(self, row: int):
        """Remove an entry from the table."""
        if row < len(self.coupon_entries):
            self.coupon_entries.pop(row)
            self.entries_table.removeRow(row)
            self.update_summary()
            
            # Update remove button connections
            for i in range(self.entries_table.rowCount()):
                btn = self.entries_table.cellWidget(i, 3)
                if btn:
                    btn.clicked.disconnect()
                    btn.clicked.connect(lambda checked, r=i: self.remove_entry(r))
    
    def update_summary(self):
        """Update the summary label."""
        total_coupons = len(self.coupon_entries)
        total_pieces = sum(qty for _, qty, _ in self.coupon_entries)
        self.summary_label.setText(f"Total Coupons: {total_coupons} | Total Pieces: {total_pieces}")
    
    def save_all(self):
        """Save all coupon entries to database using the correct method for local or API mode."""
        # Validation
        if not self.coupon_entries:
            QMessageBox.warning(self, "No Entries", "Please add at least one coupon entry.")
            return

        product_id = self.product_combo.currentData()
        medical_centre_id = self.medical_centre_combo.currentData()
        distribution_location_id = self.distribution_location_combo.currentData()

        if not product_id or not medical_centre_id or not distribution_location_id:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select product, MOH health centre, and distribution location."
            )
            return

        try:
            # Check for duplicate coupon references in database
            existing_refs = set()
            all_coupons = self.db_manager.get_all(PatientCoupon)
            for coupon in all_coupons:
                existing_refs.add(get_attr(coupon, 'coupon_reference', '').upper())

            duplicates = []
            for ref, _, _ in self.coupon_entries:
                if ref.upper() in existing_refs:
                    duplicates.append(ref)

            if duplicates:
                QMessageBox.warning(
                    self,
                    "Duplicate References",
                    f"The following coupon references already exist in the database:\n" +
                    "\n".join(duplicates) +
                    "\n\nPlease remove or rename them before saving."
                )
                return

            coupons_data = []
            for coupon_ref, quantity, date_received in self.coupon_entries:
                coupons_data.append({
                    'coupon_reference': coupon_ref,
                    'patient_name': None,
                    'cpr': None,
                    'product_id': product_id,
                    'quantity_pieces': quantity,
                    'medical_centre_id': medical_centre_id,
                    'distribution_location_id': distribution_location_id,
                    'verified': False,
                    'date_received': date_received.isoformat() if hasattr(date_received, 'isoformat') else str(date_received),
                    'notes': None
                })

            # Detect if using API client or local manager
            from src.database.db_client import DatabaseClient
            if isinstance(self.db_manager, DatabaseClient):
                result = self.db_manager.create_patient_coupons_batch(coupons_data)
                success_count = result.get('count', len(coupons_data)) if isinstance(result, dict) else len(coupons_data)
            else:
                created = self.db_manager.create_patient_coupons_batch(coupons_data)
                success_count = len(created)

            product_name = self.product_combo.currentText()
            total_pieces = sum(qty for _, qty, _ in self.coupon_entries)

            # Get date range for display
            dates = [dt for _, _, dt in self.coupon_entries]
            min_date = min(dates).strftime("%d/%m/%Y")
            max_date = max(dates).strftime("%d/%m/%Y")
            date_range = f"{min_date} to {max_date}" if min_date != max_date else min_date

            QMessageBox.information(
                self,
                "Success",
                f"Successfully added {success_count} coupons!\n\n"
                f"Product: {product_name}\n"
                f"Date Range: {date_range}\n"
                f"Total Pieces: {total_pieces}\n"
                f"Status: Pending verification"
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Coupons",
                f"Failed to save coupons:\n{str(e)}"
            )
