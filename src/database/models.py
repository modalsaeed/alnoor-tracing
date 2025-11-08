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
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    purchase_orders = relationship('PurchaseOrder', back_populates='product', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', reference='{self.reference}')>"
    
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    product = relationship('Product', back_populates='purchase_orders')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_quantity_positive'),
        CheckConstraint('remaining_stock >= 0', name='check_remaining_stock_positive'),
        CheckConstraint('remaining_stock <= quantity', name='check_remaining_not_exceed_quantity'),
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


class DistributionLocation(Base):
    """Distribution locations where products are sent."""
    
    __tablename__ = 'distribution_locations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    reference = Column(String(100), unique=True, nullable=False, index=True)
    address = Column(Text, nullable=True)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    coupons = relationship('PatientCoupon', back_populates='distribution_location')
    
    def __repr__(self):
        return f"<DistributionLocation(id={self.id}, name='{self.name}', reference='{self.reference}')>"
    
    @validates('reference')
    def validate_reference(self, key, value):
        if not value or not value.strip():
            raise ValueError("Distribution location reference cannot be empty")
        return value.strip().upper()


class MedicalCentre(Base):
    """Medical centres that issue patient coupons."""
    
    __tablename__ = 'medical_centres'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    reference = Column(String(100), unique=True, nullable=False, index=True)
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
        if not value or not value.strip():
            raise ValueError("Medical centre reference cannot be empty")
        return value.strip().upper()


class PatientCoupon(Base):
    """Patient coupons for tracking product distribution and verification."""
    
    __tablename__ = 'patient_coupons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_name = Column(String(255), nullable=False)
    cpr = Column(String(20), nullable=False, index=True)  # Civil Personal Registration number
    quantity_pieces = Column(Integer, nullable=False)
    coupon_reference = Column(String(100), unique=True, nullable=False, index=True)
    medical_centre_id = Column(Integer, ForeignKey('medical_centres.id'), nullable=False)
    distribution_location_id = Column(Integer, ForeignKey('distribution_locations.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)  # Optional product link
    verified = Column(Boolean, default=False, nullable=False, index=True)
    verification_reference = Column(String(100), nullable=True)
    date_received = Column(DateTime, default=datetime.utcnow, nullable=False)
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
        if not value or not value.strip():
            raise ValueError("CPR cannot be empty")
        # Remove any spaces or dashes for consistency
        return value.strip().replace('-', '').replace(' ', '')


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
        allowed_actions = ['CREATE', 'UPDATE', 'DELETE', 'VERIFY', 'EXPORT', 'IMPORT', 'BACKUP']
        if value.upper() not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return value.upper()
