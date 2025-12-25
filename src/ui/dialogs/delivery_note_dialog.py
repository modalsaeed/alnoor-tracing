"""
Delivery Note Dialog - Generate delivery notes from verified coupons.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QDateEdit, QSpinBox,
    QGroupBox, QMessageBox, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon, MedicalCentre, DistributionLocation, Product, PurchaseOrder
from src.utils import Colors, StyleSheets
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class DeliveryNoteDialog(QDialog):
    """Dialog for generating delivery notes from coupons."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.filtered_coupons = []
        self.selected_product = None
        self.selected_centre = None
        self.selected_location = None
        
        self.setWindowTitle("Generate Delivery Note")
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        
        self.setup_ui()
        self.load_filter_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📄 Generate Delivery Note")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Info message
        info = QLabel(
            "Select filters to find unverified coupons, then generate a delivery note.\n"
            "The delivery note will be saved as an Excel file."
        )
        info.setStyleSheet(
            "background-color: #e3f2fd; padding: 10px; border-radius: 4px; "
            "color: #1565c0; border-left: 4px solid #2196f3;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addSpacing(15)
        
        # Filters section
        filters_group = QGroupBox("Filters (Select coupons to include)")
        filters_layout = QFormLayout()
        
        # Health Centre filter
        self.centre_combo = QComboBox()
        self.centre_combo.currentIndexChanged.connect(self.apply_filters)
        filters_layout.addRow("MOH Health Centre: *", self.centre_combo)
        
        # Distribution Location filter
        self.location_combo = QComboBox()
        self.location_combo.currentIndexChanged.connect(self.apply_filters)
        filters_layout.addRow("Distribution Location:", self.location_combo)
        
        # Purchase Order filter
        self.po_combo = QComboBox()
        filters_layout.addRow("PO Reference: *", self.po_combo)
        
        # Date range
        date_layout = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.dateChanged.connect(self.apply_filters)
        date_layout.addWidget(self.date_from)
        
        date_layout.addWidget(QLabel("to"))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.apply_filters)
        date_layout.addWidget(self.date_to)
        
        filters_layout.addRow("Date Range:", date_layout)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # Preview section
        preview_group = QGroupBox("Coupon Preview (Unverified only)")
        preview_layout = QVBoxLayout()
        
        # Summary label
        self.summary_label = QLabel("No coupons match the selected filters")
        self.summary_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        preview_layout.addWidget(self.summary_label)
        
        # Table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(6)
        self.preview_table.setHorizontalHeaderLabels([
            "Coupon Ref", "Patient Name", "CPR", "Product", "Quantity", "Date Received"
        ])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setMaximumHeight(250)
        preview_layout.addWidget(self.preview_table)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Delivery details section
        details_group = QGroupBox("Delivery Note Details")
        details_layout = QFormLayout()
        
        # Pieces per carton
        self.pieces_per_carton_input = QSpinBox()
        self.pieces_per_carton_input.setRange(1, 10000)
        self.pieces_per_carton_input.setValue(1)
        self.pieces_per_carton_input.setSuffix(" pieces")
        details_layout.addRow("Pieces per Carton: *", self.pieces_per_carton_input)
        
        # Calculated values display
        self.total_pieces_label = QLabel("0")
        self.total_pieces_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        details_layout.addRow("Total Pieces:", self.total_pieces_label)
        
        self.total_cartons_label = QLabel("0")
        self.total_cartons_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        details_layout.addRow("Total Cartons:", self.total_cartons_label)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.generate_btn = QPushButton("📄 Generate Delivery Note")
        self.generate_btn.clicked.connect(self.generate_delivery_note)
        self.generate_btn.setStyleSheet(StyleSheets.button_primary(Colors.SUCCESS))
        self.generate_btn.setEnabled(False)
        button_layout.addWidget(self.generate_btn)
        
        layout.addLayout(button_layout)
    
    def load_filter_data(self):
        """Load data for filters."""
        try:
            # Load health centres
            centres = sorted(self.db_manager.get_all(MedicalCentre), key=lambda x: get_name(x))
            self.centre_combo.addItem("-- Select Health Centre --", None)
            for centre in centres:
                self.centre_combo.addItem(get_name(centre), get_id(centre))
            
            # Load distribution locations
            locations = sorted(self.db_manager.get_all(DistributionLocation), key=lambda x: get_name(x))
            self.location_combo.addItem("-- Select Distribution Location --", None)
            for location in locations:
                self.location_combo.addItem(get_name(location), get_id(location))
            
            # Load purchase orders
            pos = sorted(self.db_manager.get_all(PurchaseOrder), key=lambda x: get_attr(x, 'po_reference', ''))
            self.po_combo.addItem("-- Select PO Reference --", None)
            for po in pos:
                display_text = f"{get_attr(po, 'po_reference', 'N/A')}"
                product_name = get_nested_attr(po, 'product.name')
                if product_name:
                    display_text += f" ({product_name})"
                self.po_combo.addItem(display_text, get_id(po))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load filter data: {str(e)}")
    
    def apply_filters(self):
        """Apply filters and update preview."""
        centre_id = self.centre_combo.currentData()
        location_id = self.location_combo.currentData()
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        
        # Clear previous results
        self.filtered_coupons = []
        self.selected_product = None
        self.selected_centre = None
        self.selected_location = None
        
        # Centre must be selected, location is optional
        if not centre_id:
            self.update_preview()
            return
        
        try:
            # Get all coupons and filter
            all_coupons = self.db_manager.get_all(PatientCoupon)
            date_from_dt = datetime.combine(date_from, datetime.min.time())
            date_to_dt = datetime.combine(date_to, datetime.max.time())
            
            coupons = [
                c for c in all_coupons
                if get_attr(c, 'verified', True) == False
                and get_attr(c, 'medical_centre_id') == centre_id
                and get_attr(c, 'date_received')
                and date_from_dt <= get_attr(c, 'date_received') <= date_to_dt
                and (not location_id or get_attr(c, 'distribution_location_id') == location_id)
            ]
            
            # Group by product
            product_groups = {}
            for coupon in coupons:
                product_id = get_attr(coupon, 'product_id')
                if product_id:
                    if product_id not in product_groups:
                        product_groups[product_id] = []
                    product_groups[product_id].append(coupon)
            
            # For simplicity, we'll handle one product at a time
            # If multiple products, warn the user
            if len(product_groups) > 1:
                QMessageBox.warning(
                    self,
                    "Multiple Products",
                    f"Found coupons for {len(product_groups)} different products.\n"
                    "Delivery notes are generated per product.\n"
                    "Please generate separate delivery notes for each product."
                )
                self.filtered_coupons = []
            elif len(product_groups) == 1:
                product_id = list(product_groups.keys())[0]
                self.filtered_coupons = product_groups[product_id]
                all_products = self.db_manager.get_all(Product)
                all_centres = self.db_manager.get_all(MedicalCentre)
                all_locations = self.db_manager.get_all(DistributionLocation)
                self.selected_product = next((p for p in all_products if get_id(p) == product_id), None)
                self.selected_centre = next((c for c in all_centres if get_id(c) == centre_id), None)
                self.selected_location = next((l for l in all_locations if get_id(l) == location_id), None) if location_id else None
            else:
                self.filtered_coupons = []
            
            self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to filter coupons: {str(e)}")
    
    def update_preview(self):
        """Update the preview table and summary."""
        # Update table
        self.preview_table.setRowCount(0)
        
        total_pieces = 0
        for coupon in self.filtered_coupons:
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            
            self.preview_table.setItem(row, 0, QTableWidgetItem(coupon.coupon_reference))
            self.preview_table.setItem(row, 1, QTableWidgetItem(coupon.patient_name or "N/A"))
            self.preview_table.setItem(row, 2, QTableWidgetItem(coupon.cpr or "N/A"))
            
            product_name = coupon.product.name if coupon.product else "N/A"
            self.preview_table.setItem(row, 3, QTableWidgetItem(product_name))
            
            self.preview_table.setItem(row, 4, QTableWidgetItem(str(coupon.quantity_pieces)))
            
            date_str = coupon.date_received.strftime("%d/%m/%Y")
            self.preview_table.setItem(row, 5, QTableWidgetItem(date_str))
            
            total_pieces += coupon.quantity_pieces
        
        # Update summary
        if self.filtered_coupons:
            self.summary_label.setText(
                f"Found {len(self.filtered_coupons)} coupon(s) | "
                f"Product: {self.selected_product.name if self.selected_product else 'N/A'} | "
                f"Total: {total_pieces} pieces"
            )
            self.generate_btn.setEnabled(True)
        else:
            self.summary_label.setText("No coupons match the selected filters")
            self.generate_btn.setEnabled(False)
        
        # Update calculated values
        self.total_pieces_label.setText(str(total_pieces))
        pieces_per_carton = self.pieces_per_carton_input.value()
        total_cartons = total_pieces / pieces_per_carton if pieces_per_carton > 0 else 0
        self.total_cartons_label.setText(f"{total_cartons:.2f}")
        
        # Connect pieces per carton change
        self.pieces_per_carton_input.valueChanged.connect(self.update_carton_calculation)
    
    def update_carton_calculation(self):
        """Update carton calculation when pieces per carton changes."""
        total_pieces = sum(c.quantity_pieces for c in self.filtered_coupons)
        pieces_per_carton = self.pieces_per_carton_input.value()
        total_cartons = total_pieces / pieces_per_carton if pieces_per_carton > 0 else 0
        self.total_cartons_label.setText(f"{total_cartons:.2f}")
    
    def generate_delivery_note(self):
        """Generate the delivery note Excel file."""
        if not self.filtered_coupons:
            QMessageBox.warning(self, "No Data", "No coupons selected for delivery note.")
            return
        
        if not self.selected_product or not self.selected_centre:
            QMessageBox.warning(self, "Missing Data", "Product or Health Centre information is missing.")
            return
        
        # Validate PO is selected
        po_id = self.po_combo.currentData()
        if not po_id:
            QMessageBox.warning(self, "Missing PO", "Please select a PO reference.")
            return
        
        # Get selected PO
        try:
            all_pos = self.db_manager.get_all(PurchaseOrder)
            selected_po = next((po for po in all_pos if get_id(po) == po_id), None)
            if not selected_po:
                QMessageBox.warning(self, "Error", "Selected PO not found.")
                return
            po_reference = get_attr(selected_po, 'po_reference', 'N/A')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get PO reference: {str(e)}")
            return
        
        # Ask user where to save the file
        default_filename = f"DeliveryNote_{self.selected_centre.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Delivery Note",
            str(Path.home() / "Documents" / default_filename),
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            from openpyxl import Workbook, load_workbook
            from openpyxl.styles import Font, Alignment, Border, Side
            import sys
            
            # Check if template exists - handle frozen executable
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_path = Path(sys._MEIPASS)
            else:
                # Running as script
                base_path = Path(__file__).parent.parent.parent.parent
            
            template_path = base_path / "resources" / "templates" / "delivery_note_template.xlsx"
            
            if template_path.exists():
                # Load template
                wb = load_workbook(template_path)
                ws = wb.active
            else:
                # Create new workbook if no template
                wb = Workbook()
                ws = wb.active
            
            # Generate delivery note number
            dn_number = self.generate_delivery_note_number()
            
            # Calculate values
            total_pieces = sum(c.quantity_pieces for c in self.filtered_coupons)
            pieces_per_carton = self.pieces_per_carton_input.value()
            total_cartons = total_pieces / pieces_per_carton
            
            # Fill the cells
            # C2: Delivery Note number
            ws['C2'] = f"Delivery Note: {dn_number}"
            
            # C3: Health Centre name
            ws['C3'] = f"Ref: {self.selected_centre.name}"
            
            # C4: PO reference
            ws['C4'] = f"Ref: {po_reference}"
            
            # E2: Current date
            ws['E2'] = f"Date: {datetime.now().strftime('%d-%b-%Y')}"
            
            # C13: Product Reference
            ws['C13'] = self.selected_product.reference if self.selected_product.reference else ""
            
            # C14: Product Name
            ws['C14'] = self.selected_product.name
            
            # F14: Total pieces
            ws['F14'] = total_pieces
            
            # E14: Pieces per carton
            ws['E14'] = pieces_per_carton
            
            # D14: Number of cartons
            ws['D14'] = total_cartons
            
            # F20: Same as F14
            ws['F20'] = total_pieces
            
            # Save the workbook
            wb.save(file_path)
            
            # Update coupon delivery notes
            self.update_coupon_delivery_notes(dn_number)
            
            QMessageBox.information(
                self,
                "Success",
                f"Delivery note generated successfully!\n\n"
                f"Delivery Note: {dn_number}\n"
                f"File saved to: {file_path}\n\n"
                f"Total Coupons: {len(self.filtered_coupons)}\n"
                f"Total Pieces: {total_pieces}\n"
                f"Total Cartons: {total_cartons:.2f}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate delivery note:\n{str(e)}"
            )
    
    def generate_delivery_note_number(self) -> str:
        """Generate auto-incremented delivery note number."""
        try:
            with self.db_manager.get_session() as session:
                # Get the highest delivery note number
                coupons = session.query(PatientCoupon).filter(
                    PatientCoupon.delivery_note_number.isnot(None)
                ).all()
                
                max_number = 0
                for coupon in coupons:
                    dn = coupon.delivery_note_number
                    if dn and dn.startswith("DNM-"):
                        try:
                            num = int(dn.split("-")[1])
                            max_number = max(max_number, num)
                        except (IndexError, ValueError):
                            pass
                
                next_number = max_number + 1
                return f"DNM-{next_number:05d}"
        except Exception as e:
            print(f"Error generating delivery note number: {e}")
            # Fallback to timestamp-based number
            return f"DNM-{int(datetime.now().timestamp())}"
    
    def update_coupon_delivery_notes(self, dn_number: str):
        """Update the delivery note number for all coupons in this batch."""
        try:
            with self.db_manager.get_session() as session:
                for coupon in self.filtered_coupons:
                    db_coupon = session.query(PatientCoupon).get(coupon.id)
                    if db_coupon:
                        db_coupon.delivery_note_number = dn_number
                session.commit()
        except Exception as e:
            print(f"Error updating coupon delivery notes: {e}")
