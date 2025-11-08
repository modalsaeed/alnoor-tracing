"""
Unit Tests for Database Models

Tests all database models in src/database/models.py
"""

import unittest
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.models import (
    Base,
    Product,
    PurchaseOrder,
    DistributionLocation,
    MedicalCentre,
    PatientCoupon
)


class TestDatabaseModels(unittest.TestCase):
    """Base class for database model tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests."""
        # Use in-memory SQLite for testing
        cls.engine = create_engine('sqlite:///:memory:', echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
    
    def setUp(self):
        """Set up a fresh session for each test."""
        self.session = self.Session()
    
    def tearDown(self):
        """Clean up after each test."""
        self.session.rollback()
        self.session.close()
        # Clear all data
        for table in reversed(Base.metadata.sorted_tables):
            self.session.execute(table.delete())
        self.session.commit()


class TestProductModel(TestDatabaseModels):
    """Test Product model."""
    
    def test_create_product(self):
        """Test creating a product."""
        product = Product(
            name="Test Product",
            reference="PROD-001",
            description="Test description"
        )
        self.session.add(product)
        self.session.commit()
        
        self.assertIsNotNone(product.id)
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.reference, "PROD-001")
        self.assertIsNotNone(product.created_at)
        
    def test_product_reference_uppercase(self):
        """Test that product reference is converted to uppercase."""
        product = Product(
            name="Test Product",
            reference="prod-001"
        )
        self.session.add(product)
        self.session.commit()
        
        self.assertEqual(product.reference, "PROD-001")
        
    def test_product_unique_reference(self):
        """Test that product references must be unique."""
        product1 = Product(name="Product 1", reference="PROD-001")
        product2 = Product(name="Product 2", reference="PROD-001")
        
        self.session.add(product1)
        self.session.commit()
        
        self.session.add(product2)
        with self.assertRaises(IntegrityError):
            self.session.commit()
            
    def test_product_empty_reference(self):
        """Test that empty reference is not allowed."""
        with self.assertRaises(ValueError):
            product = Product(name="Test", reference="")
            self.session.add(product)
            self.session.flush()  # Force validation
            
    def test_product_relationship_with_po(self):
        """Test Product-PurchaseOrder relationship."""
        product = Product(name="Test Product", reference="PROD-001")
        self.session.add(product)
        self.session.commit()
        
        po = PurchaseOrder(
            po_reference="PO-001",
            product_id=product.id,
            quantity=100,
            remaining_stock=100
        )
        self.session.add(po)
        self.session.commit()
        
        self.assertEqual(len(product.purchase_orders), 1)
        self.assertEqual(product.purchase_orders[0].po_reference, "PO-001")
        
    def test_product_cascade_delete(self):
        """Test that deleting product cascades to POs."""
        product = Product(name="Test Product", reference="PROD-001")
        self.session.add(product)
        self.session.commit()
        
        po = PurchaseOrder(
            po_reference="PO-001",
            product_id=product.id,
            quantity=100,
            remaining_stock=100
        )
        self.session.add(po)
        self.session.commit()
        
        po_id = po.id
        
        # Delete product
        self.session.delete(product)
        self.session.commit()
        
        # PO should be deleted too
        deleted_po = self.session.query(PurchaseOrder).filter_by(id=po_id).first()
        self.assertIsNone(deleted_po)


class TestPurchaseOrderModel(TestDatabaseModels):
    """Test PurchaseOrder model."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create a product for PO tests
        self.product = Product(name="Test Product", reference="PROD-001")
        self.session.add(self.product)
        self.session.commit()
    
    def test_create_purchase_order(self):
        """Test creating a purchase order."""
        po = PurchaseOrder(
            po_reference="PO-001",
            product_id=self.product.id,
            quantity=100,
            remaining_stock=100,
            warehouse_location="Warehouse A"
        )
        self.session.add(po)
        self.session.commit()
        
        self.assertIsNotNone(po.id)
        self.assertEqual(po.po_reference, "PO-001")
        self.assertEqual(po.quantity, 100)
        self.assertEqual(po.remaining_stock, 100)
        
    def test_po_reference_uppercase(self):
        """Test that PO reference is converted to uppercase."""
        po = PurchaseOrder(
            po_reference="po-001",
            product_id=self.product.id,
            quantity=100,
            remaining_stock=100
        )
        self.session.add(po)
        self.session.commit()
        
        self.assertEqual(po.po_reference, "PO-001")
        
    def test_po_unique_reference(self):
        """Test that PO references must be unique."""
        po1 = PurchaseOrder(
            po_reference="PO-001",
            product_id=self.product.id,
            quantity=100,
            remaining_stock=100
        )
        po2 = PurchaseOrder(
            po_reference="PO-001",
            product_id=self.product.id,
            quantity=50,
            remaining_stock=50
        )
        
        self.session.add(po1)
        self.session.commit()
        
        self.session.add(po2)
        with self.assertRaises(IntegrityError):
            self.session.commit()
            
    def test_po_negative_quantity(self):
        """Test that negative quantity is not allowed."""
        with self.assertRaises(ValueError):
            po = PurchaseOrder(
                po_reference="PO-001",
                product_id=self.product.id,
                quantity=-10,
                remaining_stock=0
            )
            self.session.add(po)
            self.session.flush()  # Force validation
            
    def test_po_remaining_exceeds_quantity(self):
        """Test that remaining stock cannot exceed quantity."""
        po = PurchaseOrder(
            po_reference="PO-001",
            product_id=self.product.id,
            quantity=100,
            remaining_stock=150
        )
        self.session.add(po)
        
        with self.assertRaises(IntegrityError):
            self.session.commit()
            
    def test_po_stock_deduction(self):
        """Test deducting stock from PO."""
        po = PurchaseOrder(
            po_reference="PO-001",
            product_id=self.product.id,
            quantity=100,
            remaining_stock=100
        )
        self.session.add(po)
        self.session.commit()
        
        # Deduct stock
        po.remaining_stock = 80
        self.session.commit()
        
        # Verify
        updated_po = self.session.query(PurchaseOrder).filter_by(id=po.id).first()
        self.assertEqual(updated_po.remaining_stock, 80)


class TestDistributionLocationModel(TestDatabaseModels):
    """Test DistributionLocation model."""
    
    def test_create_distribution_location(self):
        """Test creating a distribution location."""
        location = DistributionLocation(
            name="Test Location",
            reference="LOC-001",
            address="123 Test St",
            contact_person="John Doe",
            phone="12345678"
        )
        self.session.add(location)
        self.session.commit()
        
        self.assertIsNotNone(location.id)
        self.assertEqual(location.name, "Test Location")
        self.assertEqual(location.reference, "LOC-001")
        
    def test_location_unique_reference(self):
        """Test that location references must be unique."""
        loc1 = DistributionLocation(name="Location 1", reference="LOC-001")
        loc2 = DistributionLocation(name="Location 2", reference="LOC-001")
        
        self.session.add(loc1)
        self.session.commit()
        
        self.session.add(loc2)
        with self.assertRaises(IntegrityError):
            self.session.commit()
            
    def test_location_relationship_with_coupon(self):
        """Test DistributionLocation-Coupon relationship."""
        location = DistributionLocation(name="Test Location", reference="LOC-001")
        self.session.add(location)
        self.session.commit()
        
        # Create medical centre for coupon
        centre = MedicalCentre(name="Test Centre", reference="MC-001")
        self.session.add(centre)
        self.session.commit()
        
        # Create product for coupon
        product = Product(name="Test Product", reference="PROD-001")
        self.session.add(product)
        self.session.commit()
        
        coupon = PatientCoupon(
            cpr="123456789",
            patient_name="Test Patient",
            coupon_reference="CPN-001",
            quantity_pieces=10,
            medical_centre_id=centre.id,
            distribution_location_id=location.id,
            product_id=product.id
        )
        self.session.add(coupon)
        self.session.commit()
        
        self.assertEqual(len(location.coupons), 1)
        self.assertEqual(location.coupons[0].patient_name, "Test Patient")


class TestMedicalCentreModel(TestDatabaseModels):
    """Test MedicalCentre model."""
    
    def test_create_medical_centre(self):
        """Test creating a medical centre."""
        centre = MedicalCentre(
            name="Test Centre",
            reference="MC-001",
            address="456 Medical St",
            contact_person="Dr. Smith",
            phone="87654321"
        )
        self.session.add(centre)
        self.session.commit()
        
        self.assertIsNotNone(centre.id)
        self.assertEqual(centre.name, "Test Centre")
        self.assertEqual(centre.reference, "MC-001")
        
    def test_centre_unique_reference(self):
        """Test that centre references must be unique."""
        centre1 = MedicalCentre(name="Centre 1", reference="MC-001")
        centre2 = MedicalCentre(name="Centre 2", reference="MC-001")
        
        self.session.add(centre1)
        self.session.commit()
        
        self.session.add(centre2)
        with self.assertRaises(IntegrityError):
            self.session.commit()


class TestCouponModel(TestDatabaseModels):
    """Test PatientCoupon model."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create required related records
        self.product = Product(name="Test Product", reference="PROD-001")
        self.centre = MedicalCentre(name="Test Centre", reference="MC-001")
        self.location = DistributionLocation(name="Test Location", reference="LOC-001")
        
        self.session.add_all([self.product, self.centre, self.location])
        self.session.commit()
    
    def test_create_coupon(self):
        """Test creating a coupon."""
        coupon = PatientCoupon(
            cpr="123456789",
            patient_name="Test Patient",
            coupon_reference="CPN-001",
            quantity_pieces=10,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        self.session.add(coupon)
        self.session.commit()
        
        self.assertIsNotNone(coupon.id)
        self.assertEqual(coupon.cpr, "123456789")
        self.assertFalse(coupon.verified)
        self.assertIsNone(coupon.date_verified)
        
    def test_coupon_reference_uppercase(self):
        """Test that coupon reference is converted to uppercase."""
        coupon = PatientCoupon(
            cpr="123456789",
            patient_name="Test Patient",
            coupon_reference="cpn-001",
            quantity_pieces=10,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        self.session.add(coupon)
        self.session.commit()
        
        self.assertEqual(coupon.coupon_reference, "CPN-001")
        
    def test_coupon_verification(self):
        """Test verifying a coupon."""
        coupon = PatientCoupon(
            cpr="123456789",
            patient_name="Test Patient",
            coupon_reference="CPN-001",
            quantity_pieces=10,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        self.session.add(coupon)
        self.session.commit()
        
        # Verify coupon
        coupon.verified = True
        coupon.date_verified = datetime.utcnow()
        coupon.verification_reference = "VER-001"
        self.session.commit()
        
        verified_coupon = self.session.query(PatientCoupon).filter_by(id=coupon.id).first()
        self.assertTrue(verified_coupon.verified)
        self.assertIsNotNone(verified_coupon.date_verified)
        self.assertEqual(verified_coupon.verification_reference, "VER-001")
        
    def test_coupon_relationships(self):
        """Test Coupon relationships."""
        coupon = PatientCoupon(
            cpr="123456789",
            patient_name="Test Patient",
            coupon_reference="CPN-001",
            quantity_pieces=10,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        self.session.add(coupon)
        self.session.commit()
        
        # Test relationships
        self.assertEqual(coupon.product.reference, "PROD-001")
        self.assertEqual(coupon.medical_centre.reference, "MC-001")
        self.assertEqual(coupon.distribution_location.reference, "LOC-001")
        
    def test_coupon_cpr_formatting(self):
        """Test CPR formatting (removes spaces and dashes)."""
        coupon = PatientCoupon(
            cpr="123-456-789",
            patient_name="Test Patient",
            coupon_reference="CPN-001",
            quantity_pieces=10,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        self.session.add(coupon)
        self.session.commit()
        
        self.assertEqual(coupon.cpr, "123456789")
        
    def test_coupon_zero_quantity_not_allowed(self):
        """Test that zero quantity is not allowed."""
        with self.assertRaises(ValueError):
            coupon = PatientCoupon(
                cpr="123456789",
                patient_name="Test Patient",
                coupon_reference="CPN-001",
                quantity_pieces=0,
                medical_centre_id=self.centre.id,
                distribution_location_id=self.location.id,
                product_id=self.product.id
            )
            self.session.add(coupon)
            self.session.flush()  # Force validation
            
    def test_coupon_unique_reference(self):
        """Test that coupon references must be unique."""
        coupon1 = PatientCoupon(
            cpr="123456789",
            patient_name="Patient 1",
            coupon_reference="CPN-001",
            quantity_pieces=10,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        
        coupon2 = PatientCoupon(
            cpr="987654321",
            patient_name="Patient 2",
            coupon_reference="CPN-001",
            quantity_pieces=5,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        
        self.session.add(coupon1)
        self.session.commit()
        
        self.session.add(coupon2)
        with self.assertRaises(IntegrityError):
            self.session.commit()


class TestModelUpdates(TestDatabaseModels):
    """Test model update behavior."""
    
    def test_product_updated_at(self):
        """Test that updated_at changes on update."""
        product = Product(name="Test Product", reference="PROD-001")
        self.session.add(product)
        self.session.commit()
        
        original_updated_at = product.updated_at
        
        # Update product
        import time
        time.sleep(0.1)  # Small delay to ensure timestamp changes
        product.name = "Updated Product"
        self.session.commit()
        
        # updated_at should change
        self.assertNotEqual(product.updated_at, original_updated_at)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
