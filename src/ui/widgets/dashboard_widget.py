"""
Dashboard Widget - Main overview and key metrics display.

Provides at-a-glance view of system status, statistics, and recent activity.
"""

from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from database import DatabaseManager, Product, PurchaseOrder, PatientCoupon, MedicalCentre, DistributionLocation
from services import StockService
from utils import Colors, Fonts, Spacing, Sizes, StyleSheets, IconStyles, get_card_color


class DashboardWidget(QWidget):
    """Dashboard widget showing key metrics and system overview."""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.stock_service = StockService(db_manager)
        self.init_ui()
        self.load_dashboard_data()
        
        # Auto-refresh every 60 seconds
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_dashboard_data)
        self.refresh_timer.start(60000)  # 60 seconds
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main scroll area to handle overflow
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel(f"{IconStyles.DASHBOARD} Dashboard")
        title.setStyleSheet(f"""
            font-size: {Fonts.SIZE_HUGE}px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Last updated label
        self.last_updated_label = QLabel()
        self.last_updated_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-style: italic;
            font-size: {Fonts.SIZE_SMALL}px;
        """)
        header_layout.addWidget(self.last_updated_label)
        
        # Refresh button
        refresh_btn = QPushButton(f"{IconStyles.REFRESH} Refresh")
        refresh_btn.clicked.connect(self.load_dashboard_data)
        refresh_btn.setStyleSheet(StyleSheets.button_primary())
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # Metrics cards (2 rows for better visibility)
        # First row - 3 cards
        metrics_row1 = QHBoxLayout()
        
        self.products_card = self.create_metric_card(f"{IconStyles.PRODUCTS} Products", "0", get_card_color('products'))
        self.pos_card = self.create_metric_card(f"{IconStyles.PURCHASE_ORDERS} Purchase Orders", "0", get_card_color('pos'))
        self.coupons_card = self.create_metric_card(f"{IconStyles.COUPONS} Total Coupons", "0", get_card_color('coupons'))
        
        metrics_row1.addWidget(self.products_card)
        metrics_row1.addWidget(self.pos_card)
        metrics_row1.addWidget(self.coupons_card)
        
        layout.addLayout(metrics_row1)
        layout.addSpacing(15)
        
        # Second row - 4 cards (coupons breakdown and locations)
        metrics_row2 = QHBoxLayout()
        
        self.verified_card = self.create_metric_card(f"{IconStyles.VERIFIED} Verified", "0", Colors.SUCCESS)
        self.pending_card = self.create_metric_card(f"{IconStyles.PENDING} Pending", "0", Colors.WARNING)
        self.centres_card = self.create_metric_card(f"{IconStyles.CENTRES} Medical Centres", "0", get_card_color('centres'))
        self.locations_card = self.create_metric_card(f"{IconStyles.LOCATIONS} Distribution Locations", "0", get_card_color('locations'))
        
        metrics_row2.addWidget(self.verified_card)
        metrics_row2.addWidget(self.pending_card)
        metrics_row2.addWidget(self.centres_card)
        metrics_row2.addWidget(self.locations_card)
        
        layout.addLayout(metrics_row2)
        layout.addSpacing(30)
        
        # Stock alerts section
        stock_section = QLabel(f"{IconStyles.WARNING} Stock Alerts")
        stock_section.setStyleSheet(f"""
            font-size: {Fonts.SIZE_LARGE}px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(stock_section)
        
        self.stock_alerts_frame = QFrame()
        self.stock_alerts_frame.setStyleSheet(StyleSheets.alert_box('warning'))
        self.stock_alerts_layout = QVBoxLayout(self.stock_alerts_frame)
        
        self.stock_alerts_label = QLabel("Checking stock levels...")
        self.stock_alerts_label.setWordWrap(True)
        self.stock_alerts_layout.addWidget(self.stock_alerts_label)
        
        layout.addWidget(self.stock_alerts_frame)
        layout.addSpacing(30)
        
        # Recent activity section
        activity_section = QLabel("📅 Recent Activity (Last 7 Days)")
        activity_section.setStyleSheet(f"""
            font-size: {Fonts.SIZE_LARGE}px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(activity_section)
        
        # Recent coupons table
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(7)
        self.recent_table.setHorizontalHeaderLabels([
            "Date", "Patient", "CPR", "Product", "Quantity", "Status", "Verification"
        ])
        
        # Configure table
        header = self.recent_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_table.setMaximumHeight(300)
        self.recent_table.setStyleSheet(StyleSheets.table())
        
        layout.addWidget(self.recent_table)
        layout.addSpacing(30)
        
        # Quick actions section
        actions_section = QLabel("⚡ Quick Actions")
        actions_section.setStyleSheet(f"""
            font-size: {Fonts.SIZE_LARGE}px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(actions_section)
        
        actions_layout = QHBoxLayout()
        
        # Quick action buttons
        add_product_btn = self.create_action_button(f"{IconStyles.ADD} Add Product", get_card_color('products'))
        add_po_btn = self.create_action_button(f"{IconStyles.PRODUCTS} Add Purchase Order", get_card_color('pos'))
        add_coupon_btn = self.create_action_button(f"{IconStyles.COUPONS} Add Coupon", get_card_color('coupons'))
        view_reports_btn = self.create_action_button(f"{IconStyles.DASHBOARD} View Reports", Colors.INFO)
        
        actions_layout.addWidget(add_product_btn)
        actions_layout.addWidget(add_po_btn)
        actions_layout.addWidget(add_coupon_btn)
        actions_layout.addWidget(view_reports_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        
        scroll.setWidget(main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def create_metric_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a metric card widget."""
        card = QFrame()
        card.setStyleSheet(StyleSheets.card(color))
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setMinimumHeight(120)
        card.setMinimumWidth(180)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(Spacing.NORMAL)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL}px;
            color: {Colors.TEXT_SECONDARY};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_HUGE}px;
            color: {color};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)
        value_label.setObjectName("value_label")  # For updating later
        layout.addWidget(value_label)
        
        layout.addStretch()
        
        return card
    
    def update_metric_card(self, card: QFrame, value: str):
        """Update the value in a metric card."""
        value_label = card.findChild(QLabel, "value_label")
        if value_label:
            value_label.setText(value)
    
    def create_action_button(self, text: str, color: str) -> QPushButton:
        """Create a quick action button."""
        btn = QPushButton(text)
        btn.setMinimumHeight(Sizes.BUTTON_HEIGHT)
        btn.setStyleSheet(StyleSheets.button_primary(color))
        
        # Connect to navigation (to be implemented)
        if "Product" in text:
            btn.clicked.connect(lambda: self.navigate_to_tab(2))  # Products tab
        elif "Purchase Order" in text:
            btn.clicked.connect(lambda: self.navigate_to_tab(1))  # PO tab
        elif "Coupon" in text:
            btn.clicked.connect(lambda: self.navigate_to_tab(5))  # Coupons tab
        elif "Reports" in text:
            btn.clicked.connect(lambda: self.navigate_to_tab(6))  # Reports tab
        
        return btn
    
    def navigate_to_tab(self, tab_index: int):
        """Navigate to a specific tab in the main window."""
        # Get parent main window and switch tab
        parent = self.parent()
        while parent:
            if hasattr(parent, 'tabs'):
                parent.tabs.setCurrentIndex(tab_index)
                break
            parent = parent.parent()
    
    def load_dashboard_data(self):
        """Load all dashboard data from database."""
        try:
            # Update timestamp
            self.last_updated_label.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get counts
            products_count = len(self.db_manager.get_all(Product))
            pos_count = len(self.db_manager.get_all(PurchaseOrder))
            coupons = self.db_manager.get_all(PatientCoupon)
            coupons_count = len(coupons)
            verified_count = sum(1 for c in coupons if c.verified)
            pending_count = coupons_count - verified_count
            centres_count = len(self.db_manager.get_all(MedicalCentre))
            locations_count = len(self.db_manager.get_all(DistributionLocation))
            
            # Update metric cards
            self.update_metric_card(self.products_card, str(products_count))
            self.update_metric_card(self.pos_card, str(pos_count))
            self.update_metric_card(self.coupons_card, str(coupons_count))
            self.update_metric_card(self.verified_card, str(verified_count))
            self.update_metric_card(self.pending_card, str(pending_count))
            self.update_metric_card(self.centres_card, str(centres_count))
            self.update_metric_card(self.locations_card, str(locations_count))
            
            # Load stock alerts
            self.load_stock_alerts()
            
            # Load recent activity
            self.load_recent_activity()
            
        except Exception as e:
            print(f"Error loading dashboard data: {e}")
    
    def load_stock_alerts(self):
        """Load and display stock alerts for low inventory."""
        try:
            # Clear existing alerts
            while self.stock_alerts_layout.count() > 0:
                item = self.stock_alerts_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Get low stock products (default 20% threshold)
            low_stock_products = self.stock_service.get_low_stock_products(threshold=0.20)
            
            if not low_stock_products:
                no_alerts = QLabel(f"{IconStyles.VERIFIED} All products have sufficient stock levels!")
                no_alerts.setStyleSheet(f"""
                    color: {Colors.SUCCESS};
                    font-weight: {Fonts.WEIGHT_BOLD};
                """)
                self.stock_alerts_layout.addWidget(no_alerts)
                
                self.stock_alerts_frame.setStyleSheet(StyleSheets.alert_box('success'))
            else:
                alert_header = QLabel(f"{IconStyles.WARNING} {len(low_stock_products)} product(s) need attention:")
                alert_header.setStyleSheet(f"""
                    font-weight: {Fonts.WEIGHT_BOLD};
                    color: {Colors.ALERT_WARNING_TEXT};
                    margin-bottom: {Spacing.NORMAL}px;
                """)
                self.stock_alerts_layout.addWidget(alert_header)
                
                for item in low_stock_products:
                    product_name = item['product_name']
                    current = item['total_remaining']
                    total = item['total_ordered']
                    percentage = item['usage_percentage']
                    remaining_pct = 100 - percentage
                    
                    alert_text = f"• {product_name}: {current} / {total} pieces ({remaining_pct:.1f}% remaining)"
                    alert_label = QLabel(alert_text)
                    alert_label.setStyleSheet(f"""
                        color: {Colors.ALERT_WARNING_TEXT};
                        padding: {Spacing.TINY}px 0;
                    """)
                    self.stock_alerts_layout.addWidget(alert_label)
                
                self.stock_alerts_frame.setStyleSheet(StyleSheets.alert_box('warning'))
                
        except Exception as e:
            error_label = QLabel(f"{IconStyles.ERROR} Error loading stock alerts: {str(e)}")
            error_label.setStyleSheet(f"color: {Colors.ERROR};")
            self.stock_alerts_layout.addWidget(error_label)
    
    def load_recent_activity(self):
        """Load recent coupon activity from last 7 days."""
        try:
            # Get coupons from last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)
            all_coupons = self.db_manager.get_all(PatientCoupon)
            
            # Filter by date and sort by newest first
            recent_coupons = [
                c for c in all_coupons 
                if c.created_at >= seven_days_ago
            ]
            recent_coupons.sort(key=lambda c: c.created_at, reverse=True)
            
            # Limit to 20 most recent
            recent_coupons = recent_coupons[:20]
            
            # Populate table
            self.recent_table.setRowCount(0)
            
            if not recent_coupons:
                # Show "no activity" message
                self.recent_table.setRowCount(1)
                no_activity = QTableWidgetItem("No recent activity in the last 7 days")
                no_activity.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.recent_table.setItem(0, 0, no_activity)
                self.recent_table.setSpan(0, 0, 1, 7)
                return
            
            for coupon in recent_coupons:
                row = self.recent_table.rowCount()
                self.recent_table.insertRow(row)
                
                # Date
                date_str = coupon.created_at.strftime("%Y-%m-%d %H:%M")
                self.recent_table.setItem(row, 0, QTableWidgetItem(date_str))
                
                # Patient
                self.recent_table.setItem(row, 1, QTableWidgetItem(coupon.patient_name))
                
                # CPR
                self.recent_table.setItem(row, 2, QTableWidgetItem(coupon.cpr))
                
                # Product
                product_name = coupon.product.name if coupon.product else "Unknown"
                self.recent_table.setItem(row, 3, QTableWidgetItem(product_name))
                
                # Quantity
                quantity_item = QTableWidgetItem(f"{coupon.quantity_pieces} pcs")
                quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.recent_table.setItem(row, 4, quantity_item)
                
                # Status
                status_text = f"{IconStyles.VERIFIED} Verified" if coupon.verified else f"{IconStyles.PENDING} Pending"
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if coupon.verified:
                    status_item.setBackground(QColor(Colors.ALERT_SUCCESS_BG))
                    status_item.setForeground(QColor(Colors.SUCCESS))
                else:
                    status_item.setBackground(QColor(Colors.ALERT_WARNING_BG))
                    status_item.setForeground(QColor(Colors.WARNING))
                self.recent_table.setItem(row, 5, status_item)
                
                # Verification
                ver_ref = coupon.verification_reference if coupon.verified else "-"
                self.recent_table.setItem(row, 6, QTableWidgetItem(ver_ref))
                
        except Exception as e:
            print(f"Error loading recent activity: {e}")
