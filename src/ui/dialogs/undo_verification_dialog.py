"""
Undo Verification Dialog - Revert recent verification actions.

Allows users to undo verification of coupon bundles in case of errors.
"""

from datetime import datetime, timedelta
from typing import List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from sqlalchemy.orm import joinedload
from src.database.db_manager import DatabaseManager
from src.database.models import PatientCoupon
from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


class UndoVerificationDialog(QDialog):
    """Dialog for undoing recent verification actions."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.bundles_data = []
        self.setup_ui()
        
        # Load recent verifications
        self.load_recent_verifications()
        
    def setup_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Undo Verification")
        self.setModal(True)
        self.resize(1100, 700)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("⏮️ Undo Recent Verifications")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(title)
        
        # Warning message
        warning = QLabel(
            "⚠️ Use this feature to undo verification in case of errors.\n"
            "Undoing verification will clear the verification reference, delivery note number, and GRV reference."
        )
        warning.setStyleSheet("""
            background-color: #fff3cd;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        """)
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Date filter section
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("📅 Show verifications from last:")
        filter_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        filter_layout.addWidget(filter_label)
        
        self.days_filter = QPushButton("7 Days")
        self.days_filter.setCheckable(True)
        self.days_filter.setChecked(True)
        self.days_filter.clicked.connect(lambda: self.set_days_filter(7))
        filter_layout.addWidget(self.days_filter)
        
        days_30_btn = QPushButton("30 Days")
        days_30_btn.setCheckable(True)
        days_30_btn.clicked.connect(lambda: self.set_days_filter(30))
        filter_layout.addWidget(days_30_btn)
        
        days_all_btn = QPushButton("All Time")
        days_all_btn.setCheckable(True)
        days_all_btn.clicked.connect(lambda: self.set_days_filter(None))
        filter_layout.addWidget(days_all_btn)
        
        # Group buttons for exclusive selection
        self.filter_buttons = [self.days_filter, days_30_btn, days_all_btn]
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_recent_verifications)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 6px 15px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Verifications table
        table_label = QLabel("📦 Recently Verified Bundles:")
        table_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(table_label)
        
        self.verifications_table = QTableWidget()
        self.verifications_table.setColumnCount(8)
        self.verifications_table.setHorizontalHeaderLabels([
            "Verification Ref", "DN Number", "Health Centre", 
            "Verified Date", "Coupons", "Pieces", "GRV", "Action"
        ])
        
        # Configure table
        header = self.verifications_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        self.verifications_table.setAlternatingRowColors(True)
        self.verifications_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verifications_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.verifications_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.verifications_table)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #95a5a6;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """)
        close_layout.addWidget(close_btn)
        
        layout.addLayout(close_layout)
    
    def set_days_filter(self, days: int = None):
        """Set the days filter and refresh."""
        # Update button states
        for btn in self.filter_buttons:
            btn.setChecked(False)
        
        if days == 7:
            self.filter_buttons[0].setChecked(True)
        elif days == 30:
            self.filter_buttons[1].setChecked(True)
        else:
            self.filter_buttons[2].setChecked(True)
        
        self.current_days_filter = days
        self.load_recent_verifications()
    
    def load_recent_verifications(self):
        """Load recently verified bundles."""
        try:
            # Calculate date filter
            if not hasattr(self, 'current_days_filter'):
                self.current_days_filter = 7
            date_filter = None
            if self.current_days_filter:
                date_filter = datetime.now() - timedelta(days=self.current_days_filter)
            # Use db_manager.get_all and helpers for compatibility
            all_coupons = self.db_manager.get_all(PatientCoupon)
            def is_recent_verified(c):
                if get_attr(c, 'verified') != True:
                    return False
                if get_attr(c, 'verification_reference') is None:
                    return False
                if not date_filter:
                    return True
                date_val = get_attr(c, 'date_verified')
                import datetime as dt
                if isinstance(date_val, dt.datetime):
                    return date_val >= date_filter
                elif isinstance(date_val, str):
                    try:
                        parsed = dt.datetime.fromisoformat(date_val)
                        return parsed >= date_filter
                    except Exception:
                        return False
                return False
            coupons = [c for c in all_coupons if is_recent_verified(c)]
            coupons = sorted(coupons, key=lambda c: get_attr(c, 'date_verified') or datetime.min, reverse=True)
            
            if not coupons:
                self.verifications_table.setRowCount(1)
                no_data = QTableWidgetItem("No recent verifications found.")
                no_data.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.verifications_table.setItem(0, 0, no_data)
                self.verifications_table.setSpan(0, 0, 1, 8)
                self.bundles_data = []
                return

            # Group by verification reference and DN number
            bundles_dict = {}
            for coupon in coupons:
                ver_ref = get_attr(coupon, 'verification_reference', 'N/A')
                dn_num = get_attr(coupon, 'delivery_note_number', 'N/A')
                key = (ver_ref, dn_num)
                if key not in bundles_dict:
                    bundles_dict[key] = []
                bundles_dict[key].append(coupon)

            # Convert to list
            self.bundles_data = []
            import datetime as dt
            def parse_dt(val):
                if isinstance(val, dt.datetime):
                    return val
                elif isinstance(val, str):
                    try:
                        return dt.datetime.fromisoformat(val)
                    except Exception:
                        return dt.datetime.min
                return dt.datetime.min
            for (ver_ref, dn_num), coupons_list in bundles_dict.items():
                # Get latest verification date
                verified_dates = [get_attr(c, 'date_verified') for c in coupons_list if get_attr(c, 'date_verified')]
                verified_date = max([parse_dt(d) for d in verified_dates]) if verified_dates else datetime.now()

                # Get health centre from first coupon
                health_centre = 'Unknown'
                first_centre = get_attr(coupons_list[0], 'medical_centre', None)
                if first_centre and hasattr(first_centre, 'name'):
                    health_centre = get_attr(first_centre, 'name', 'Unknown')
                elif isinstance(coupons_list[0], dict):
                    centre_id = get_attr(coupons_list[0], 'medical_centre_id', None)
                    health_centre = str(centre_id) if centre_id else 'Unknown'

                # Get GRV
                grv_ref = get_attr(coupons_list[0], 'grv_reference', '-')

                # Calculate totals
                total_pieces = sum(get_attr(c, 'quantity_pieces', 0) for c in coupons_list)

                self.bundles_data.append({
                    'verification_ref': ver_ref,
                    'dn_number': dn_num,
                    'health_centre': health_centre,
                    'verified_date': verified_date,
                    'coupon_count': len(coupons_list),
                    'total_pieces': total_pieces,
                    'grv_ref': grv_ref,
                    'coupons': coupons_list
                })

            # Sort by verification date (newest first)
            self.bundles_data.sort(key=lambda x: x['verified_date'], reverse=True)

            # Populate table
            self.verifications_table.setRowCount(len(self.bundles_data))
            for row, bundle in enumerate(self.bundles_data):
                # Verification Reference
                self.verifications_table.setItem(row, 0, QTableWidgetItem(bundle['verification_ref']))
                # DN Number
                self.verifications_table.setItem(row, 1, QTableWidgetItem(bundle['dn_number']))
                # Health Centre
                self.verifications_table.setItem(row, 2, QTableWidgetItem(bundle['health_centre']))
                # Verified Date
                date_str = bundle['verified_date'].strftime('%Y-%m-%d %H:%M')
                self.verifications_table.setItem(row, 3, QTableWidgetItem(date_str))
                # Coupons Count
                count_item = QTableWidgetItem(str(bundle['coupon_count']))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.verifications_table.setItem(row, 4, count_item)
                # Total Pieces
                pieces_item = QTableWidgetItem(str(bundle['total_pieces']))
                pieces_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.verifications_table.setItem(row, 5, pieces_item)
                # GRV
                grv_item = QTableWidgetItem(bundle['grv_ref'])
                if bundle['grv_ref'] != "-":
                    grv_item.setBackground(QColor("#d4edda"))
                    grv_item.setForeground(QColor("#155724"))
                self.verifications_table.setItem(row, 6, grv_item)
                # Undo button
                undo_btn = QPushButton("⏮️ Undo")
                undo_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        padding: 5px 15px;
                        border: none;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
                undo_btn.clicked.connect(lambda checked, b=bundle: self.undo_verification(b))
                self.verifications_table.setCellWidget(row, 7, undo_btn)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load verifications:\n{str(e)}"
            )
    
    def undo_verification(self, bundle: dict):
        """Undo verification for a bundle."""
        reply = QMessageBox.warning(
            self,
            "⚠️ Undo Verification",
            f"Are you sure you want to UNDO this verification?\n\n"
            f"Verification Ref: {bundle['verification_ref']}\n"
            f"DN Number: {bundle['dn_number']}\n"
            f"Health Centre: {bundle['health_centre']}\n"
            f"Coupons: {bundle['coupon_count']}\n\n"
            f"This will:\n"
            f"• Mark all coupons as unverified (pending)\n"
            f"• Clear verification reference\n"
            f"• Clear delivery note number\n"
            f"• Clear DN date\n"
            f"• Clear GRV reference\n\n"
            f"This action cannot be automatically undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                updated_count = 0
                from src.database.models import PatientCoupon
                for coupon in bundle['coupons']:
                    # Use correct update signature for local mode
                    if hasattr(self.db_manager, 'server_url'):
                        # API mode: pass dict
                        coupon_dict = dict(coupon) if isinstance(coupon, dict) else {
                            k: v for k, v in coupon.__dict__.items() if not k.startswith('_')
                        }
                        coupon_dict['verified'] = False
                        coupon_dict['verification_reference'] = None
                        coupon_dict['delivery_note_number'] = None
                        coupon_dict['date_verified'] = None
                        coupon_dict['grv_reference'] = None
                        self.db_manager.update(coupon_dict)
                    else:
                        # Local mode: use (model_class, record_id, update_fields)
                        update_fields = {
                            'verified': False,
                            'verification_reference': None,
                            'delivery_note_number': None,
                            'date_verified': None,
                            'grv_reference': None
                        }
                        # get_id helper for compatibility
                        from src.utils.model_helpers import get_id
                        self.db_manager.update(PatientCoupon, get_id(coupon), update_fields)
                    updated_count += 1
                QMessageBox.information(
                    self,
                    "Verification Undone",
                    f"✅ Successfully undone verification for {updated_count} coupon(s).\n\n"
                    f"The coupons are now back to pending status."
                )
                # Refresh the list
                self.load_recent_verifications()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Undo Error",
                    f"Failed to undo verification:\n{str(e)}"
                )
