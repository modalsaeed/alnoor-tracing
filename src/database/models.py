"""
Database models for Alnoor Medical Services Tracking App.

Using SQLAlchemy ORM for database-agnostic design,
enabling future migration to web-based system (PostgreSQL/MySQL).
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
    Numeric,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates

Base = declarative_base()


class Product(Base):
    """Product catalog with unique references."""
    
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    reference = Column(String(100), unique=True, nullable=False, index=True)
    unit = Column(String(50), nullable=True)  # e.g., "ctn", "box", "pcs", "kg"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    purchase_orders = relationship('PurchaseOrder', back_populates='product', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', reference='{self.reference}', unit='{self.unit}')>"
    
    @validates('reference')
    def validate_reference(self, key, value):
        if not value or not value.strip():
            raise ValueError("Product reference cannot be empty")
        return value.strip().upper()


class PurchaseOrder(Base):
    """Purchase orders from Ministry of Health with stock tracking."""
    
    __tablename__ = 'purchase_orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    po_reference = Column(String(100), unique=True, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=False)
    remaining_stock = Column(Integer, nullable=False)
    warehouse_location = Column(String(255), nullable=True)
    
    # Pricing fields (optional)
    unit_price = Column(Numeric(10, 3), nullable=True)  # Unit price in BHD (3 decimal places)
    tax_rate = Column(Numeric(5, 2), nullable=True)     # Tax rate as percentage (e.g., 10.00 for 10%)
    tax_amount = Column(Numeric(10, 3), nullable=True)  # Calculated tax amount in BHD
    total_without_tax = Column(Numeric(10, 3), nullable=True)  # Total before tax
    total_with_tax = Column(Numeric(10, 3), nullable=True)     # Total including tax
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    product = relationship('Product', back_populates='purchase_orders')
    # Note: Transactions now reference Purchase (supplier invoices), not PurchaseOrder
    # purchases = relationship defined in Purchase model
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_quantity_positive'),
        CheckConstraint('remaining_stock >= 0', name='check_remaining_stock_positive'),
        CheckConstraint('remaining_stock <= quantity', name='check_remaining_not_exceed_quantity'),
        CheckConstraint('unit_price IS NULL OR unit_price >= 0', name='check_unit_price_positive'),
        CheckConstraint('tax_rate IS NULL OR (tax_rate >= 0 AND tax_rate <= 100)', name='check_tax_rate_valid'),
        CheckConstraint('tax_amount IS NULL OR tax_amount >= 0', name='check_tax_amount_positive'),
        CheckConstraint('total_without_tax IS NULL OR total_without_tax >= 0', name='check_total_without_tax_positive'),
        CheckConstraint('total_with_tax IS NULL OR total_with_tax >= 0', name='check_total_with_tax_positive'),
    )
    
    def __repr__(self):
        return f"<PurchaseOrder(id={self.id}, po_ref='{self.po_reference}', qty={self.quantity}, remaining={self.remaining_stock})>"
    
    @validates('quantity', 'remaining_stock')
    def validate_quantity(self, key, value):
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @validates('po_reference')
    def validate_po_reference(self, key, value):
        if not value or not value.strip():
            raise ValueError("PO reference cannot be empty")
        return value.strip().upper()


class Purchase(Base):
    """
    Supplier purchases/invoices that fulfill Local Purchase Orders.
    
    Flow: Local PO -> Purchase (supplier invoice) -> Transaction -> Coupon
    Purchases reduce the Local PO quantity and provide stock for transactions.
    """
    
    __tablename__ = 'purchases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    remaining_stock = Column(Integer, nullable=False)  # Tracks what's left to distribute
    unit_price = Column(Numeric(10, 3), nullable=False)  # Price per unit in BHD
    total_price = Column(Numeric(10, 3), nullable=False)  # Total price (qty * unit_price)
    purchase_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    supplier_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    purchase_order = relationship('PurchaseOrder', backref='purchases')
    product = relationship('Product')
    transactions = relationship('Transaction', back_populates='purchase', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_purchase_quantity_positive'),
        CheckConstraint('remaining_stock >= 0', name='check_purchase_remaining_stock_positive'),
        CheckConstraint('remaining_stock <= quantity', name='check_purchase_remaining_not_exceed_quantity'),
        CheckConstraint('unit_price >= 0', name='check_purchase_unit_price_positive'),
        CheckConstraint('total_price >= 0', name='check_purchase_total_price_positive'),
    )
    
    def __repr__(self):
        return f"<Purchase(id={self.id}, invoice='{self.invoice_number}', qty={self.quantity}, remaining={self.remaining_stock})>"
    
    @validates('quantity', 'remaining_stock')
    def validate_quantity(self, key, value):
        if key == 'quantity' and value <= 0:
            raise ValueError("Purchase quantity must be greater than 0")
        if key == 'remaining_stock' and value < 0:
            raise ValueError("Remaining stock cannot be negative")
        return value
    
    @validates('invoice_number')
    def validate_invoice_number(self, key, value):
        if not value or not value.strip():
            raise ValueError("Invoice number cannot be empty")
        return value.strip().upper()


class Pharmacy(Base):
    """Pharmacy groups that contain multiple distribution locations/branches."""
    
    __tablename__ = 'pharmacies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    reference = Column(String(100), unique=True, nullable=True, index=True)  # Made optional
    trn = Column(String(100), nullable=True)  # Tax Registration Number
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    distribution_locations = relationship('DistributionLocation', back_populates='pharmacy', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Pharmacy(id={self.id}, name='{self.name}', reference='{self.reference}')>"
    
    @validates('reference')
    def validate_reference(self, key, value):
        if value and value.strip():
            return value.strip().upper()
        return value


class DistributionLocation(Base):
    """Distribution locations where products are sent."""
    
    __tablename__ = 'distribution_locations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    reference = Column(String(100), unique=True, nullable=True, index=True)  # Made optional
    trn = Column(String(100), nullable=True)  # Tax Registration Number
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'), nullable=True)  # Optional pharmacy grouping
    address = Column(Text, nullable=True)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    pharmacy = relationship('Pharmacy', back_populates='distribution_locations')
    coupons = relationship('PatientCoupon', back_populates='distribution_location')
    transactions = relationship('Transaction', back_populates='distribution_location', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<DistributionLocation(id={self.id}, name='{self.name}', reference='{self.reference}')>"
    
    @validates('reference')
    def validate_reference(self, key, value):
        if value and value.strip():
            return value.strip().upper()
        return value


class MedicalCentre(Base):
    """Medical centres that issue patient coupons."""
    
    __tablename__ = 'medical_centres'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    reference = Column(String(100), unique=True, nullable=True, index=True)  # Made optional
    address = Column(Text, nullable=True)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    coupons = relationship('PatientCoupon', back_populates='medical_centre')
    
    def __repr__(self):
        return f"<MedicalCentre(id={self.id}, name='{self.name}', reference='{self.reference}')>"
    
    @validates('reference')
    def validate_reference(self, key, value):
        if value and value.strip():
            return value.strip().upper()
        return value


class PatientCoupon(Base):
    """Patient coupons for tracking product distribution and verification."""
    
    __tablename__ = 'patient_coupons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_name = Column(String(255), nullable=True)  # Made optional
    cpr = Column(String(20), nullable=True, index=True)  # Made optional - Civil Personal Registration number
    quantity_pieces = Column(Integer, nullable=False)
    coupon_reference = Column(String(100), unique=True, nullable=False, index=True)
    medical_centre_id = Column(Integer, ForeignKey('medical_centres.id'), nullable=False)
    distribution_location_id = Column(Integer, ForeignKey('distribution_locations.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)  # Optional product link
    verified = Column(Boolean, default=False, nullable=False, index=True)
    verification_reference = Column(String(100), nullable=True)
    delivery_note_number = Column(String(100), nullable=True, index=True)  # NEW: Delivery note for verification
    grv_reference = Column(String(100), nullable=True, index=True)  # NEW: GRV reference number
    date_received = Column(DateTime, nullable=False)  # User-provided date
    date_verified = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    medical_centre = relationship('MedicalCentre', back_populates='coupons')
    distribution_location = relationship('DistributionLocation', back_populates='coupons')
    product = relationship('Product')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity_pieces > 0', name='check_quantity_pieces_positive'),
    )
    
    def __repr__(self):
        status = "Verified" if self.verified else "Unverified"
        return f"<PatientCoupon(id={self.id}, coupon_ref='{self.coupon_reference}', status='{status}')>"
    
    @validates('quantity_pieces')
    def validate_quantity(self, key, value):
        if value <= 0:
            raise ValueError("Quantity must be greater than 0")
        return value
    
    @validates('coupon_reference')
    def validate_coupon_reference(self, key, value):
        if not value or not value.strip():
            raise ValueError("Coupon reference cannot be empty")
        return value.strip().upper()
    
    @validates('cpr')
    def validate_cpr(self, key, value):
        # CPR is now optional
        if value and value.strip():
            # Remove any spaces or dashes for consistency
            return value.strip().replace('-', '').replace(' ', '')
        return value


class Transaction(Base):
    """
    Transactions for tracking product transfers from supplier purchases to distribution locations.
    
    New Flow: Local PO -> Purchase (supplier invoice) -> Transaction -> Coupon
    Transactions now reference Purchase (supplier invoice) instead of PO directly.
    This tracks which specific purchase batch was sent to which distribution location.
    """
    
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_reference = Column(String(100), unique=True, nullable=True, index=True)  # Made optional
    purchase_id = Column(Integer, ForeignKey('purchases.id'), nullable=False)  # Changed from purchase_order_id
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    distribution_location_id = Column(Integer, ForeignKey('distribution_locations.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    purchase = relationship('Purchase', back_populates='transactions')  # Changed from purchase_order
    product = relationship('Product')
    distribution_location = relationship('DistributionLocation', back_populates='transactions')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_transaction_quantity_positive'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, ref='{self.transaction_reference}', qty={self.quantity})>"
    
    @validates('quantity')
    def validate_quantity(self, key, value):
        if value <= 0:
            raise ValueError("Transaction quantity must be greater than 0")
        return value
    
    @validates('transaction_reference')
    def validate_transaction_reference(self, key, value):
        # Transaction reference is optional
        if value and value.strip():
            return value.strip().upper()
        return None


class ActivityLog(Base):
    """Audit trail for tracking all database operations."""
    
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, VERIFY, etc.
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    user = Column(String(100), nullable=True)  # For future multi-user support
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    old_values = Column(Text, nullable=True)  # JSON string of old values
    new_values = Column(Text, nullable=True)  # JSON string of new values
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, action='{self.action}', table='{self.table_name}', timestamp='{self.timestamp}')>"
    
    @validates('action')
    def validate_action(self, key, value):
        allowed_actions = ['CREATE', 'UPDATE', 'DELETE', 'VERIFY', 'EXPORT', 'IMPORT', 'BACKUP', 'RESTORE']
        if value.upper() not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return value.upper()
