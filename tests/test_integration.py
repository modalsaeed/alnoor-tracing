"""
Integration Tests for Coupon Verification Workflow

Tests the complete verification workflow with simpler direct database operations
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.models import Base, Product, PurchaseOrder, PatientCoupon, MedicalCentre, DistributionLocation


class TestCouponVerificationWorkflow(unittest.TestCase):
    """Test complete coupon verification workflow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests."""
        cls.engine = create_engine('sqlite:///:memory:', echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
    
    def setUp(self):
        """Set up test data for each test."""
        self.session = self.Session()
        
        # Create test product
        self.product = Product(name="Test Medicine", reference="MED-001")
        self.session.add(self.product)
        self.session.flush()
        
        # Create purchase orders with stock
        self.po1 = PurchaseOrder(
            po_reference="PO-2024-001",
            product_id=self.product.id,
            quantity=100,
            remaining_stock=100
        )
        self.po2 = PurchaseOrder(
            po_reference="PO-2024-002",
            product_id=self.product.id,
            quantity=50,
            remaining_stock=50
        )
        self.session.add_all([self.po1, self.po2])
        self.session.flush()
        
        # Create medical centre and location
        self.centre = MedicalCentre(name="Test Centre", reference="MC-001")
        self.location = DistributionLocation(name="Test Location", reference="LOC-001")
        self.session.add_all([self.centre, self.location])
        self.session.flush()
        
        self.session.commit()
    
    def tearDown(self):
        """Clean up after each test."""
        self.session.close()
        session = self.Session()
        try:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        finally:
            session.close()
    
    def deduct_stock_fifo(self, product_id, quantity):
        """Helper method to deduct stock using FIFO."""
        total_stock = self.session.query(
            func.sum(PurchaseOrder.remaining_stock)
        ).filter(
            PurchaseOrder.product_id == product_id
        ).scalar() or 0
        
        if total_stock < quantity:
            return False
        
        # Get POs with stock ordered by creation (FIFO)
        pos_with_stock = self.session.query(PurchaseOrder).filter(
            PurchaseOrder.product_id == product_id,
            PurchaseOrder.remaining_stock > 0
        ).order_by(PurchaseOrder.created_at).all()
        
        remaining_to_deduct = quantity
        for po in pos_with_stock:
            if remaining_to_deduct <= 0:
                break
            
            deduction = min(po.remaining_stock, remaining_to_deduct)
            po.remaining_stock -= deduction
            remaining_to_deduct -= deduction
        
        self.session.commit()
        return True
    
    def test_complete_verification_workflow(self):
        """Test complete coupon verification workflow."""
        # Create coupon
        coupon = PatientCoupon(
            patient_name="John Doe",
            cpr="123456789",
            coupon_reference="CPN-2024-001",
            quantity_pieces=10,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        self.session.add(coupon)
        self.session.commit()
        
        self.assertFalse(coupon.verified)
        
        # Check stock before
        stock_before = self.session.query(
            func.sum(PurchaseOrder.remaining_stock)
        ).filter(PurchaseOrder.product_id == self.product.id).scalar()
        self.assertEqual(stock_before, 150)
        
        # Deduct stock and verify
        success = self.deduct_stock_fifo(self.product.id, 10)
        self.assertTrue(success)
        
        coupon.verified = True
        coupon.date_verified = datetime.utcnow()
        coupon.verification_reference = "VER-2024-001"
        self.session.commit()
        
        # Verify results
        stock_after = self.session.query(
            func.sum(PurchaseOrder.remaining_stock)
        ).filter(PurchaseOrder.product_id == self.product.id).scalar()
        self.assertEqual(stock_after, 140)
        
        verified_coupon = self.session.query(PatientCoupon).filter_by(id=coupon.id).first()
        self.assertTrue(verified_coupon.verified)
        self.assertEqual(verified_coupon.verification_reference, "VER-2024-001")
    
    def test_insufficient_stock(self):
        """Test verification fails with insufficient stock."""
        # Try to deduct more than available
        success = self.deduct_stock_fifo(self.product.id, 200)
        self.assertFalse(success)
        
        # Stock unchanged
        stock = self.session.query(
            func.sum(PurchaseOrder.remaining_stock)
        ).filter(PurchaseOrder.product_id == self.product.id).scalar()
        self.assertEqual(stock, 150)
    
    def test_fifo_deduction(self):
        """Test FIFO stock deduction."""
        # Deduct 120 (should take 100 from PO1, 20 from PO2)
        success = self.deduct_stock_fifo(self.product.id, 120)
        self.assertTrue(success)
        
        po1 = self.session.query(PurchaseOrder).filter_by(id=self.po1.id).first()
        po2 = self.session.query(PurchaseOrder).filter_by(id=self.po2.id).first()
        
        self.assertEqual(po1.remaining_stock, 0)
        self.assertEqual(po2.remaining_stock, 30)
    
    def test_multiple_verifications(self):
        """Test multiple coupon verifications."""
        for i in range(5):
            coupon = PatientCoupon(
                patient_name=f"Patient {i+1}",
                cpr=f"12345678{i}",
                coupon_reference=f"CPN-{i+1}",
                quantity_pieces=10,
                medical_centre_id=self.centre.id,
                distribution_location_id=self.location.id,
                product_id=self.product.id
            )
            self.session.add(coupon)
            self.session.commit()
            
            self.deduct_stock_fifo(self.product.id, 10)
            coupon.verified = True
            self.session.commit()
        
        final_stock = self.session.query(
            func.sum(PurchaseOrder.remaining_stock)
        ).filter(PurchaseOrder.product_id == self.product.id).scalar()
        self.assertEqual(final_stock, 100)
        
        verified_count = self.session.query(PatientCoupon).filter_by(verified=True).count()
        self.assertEqual(verified_count, 5)
    
    def test_verification_history(self):
        """Test verification history maintenance."""
        base_time = datetime.utcnow()
        
        for i in range(3):
            coupon = PatientCoupon(
                patient_name=f"Patient {i+1}",
                cpr=f"11122233{i}",
                coupon_reference=f"CPN-10{i}",
                quantity_pieces=5,
                medical_centre_id=self.centre.id,
                distribution_location_id=self.location.id,
                product_id=self.product.id
            )
            self.session.add(coupon)
            self.session.commit()
            
            self.deduct_stock_fifo(self.product.id, 5)
            coupon.verified = True
            coupon.date_verified = base_time + timedelta(hours=i)
            self.session.commit()
        
        verified_coupons = self.session.query(PatientCoupon).filter_by(
            verified=True
        ).order_by(PatientCoupon.date_verified).all()
        
        self.assertEqual(len(verified_coupons), 3)
        for i, coupon in enumerate(verified_coupons):
            self.assertEqual(coupon.coupon_reference, f"CPN-10{i}")
    
    def test_duplicate_coupon_reference(self):
        """Test duplicate coupon references not allowed."""
        coupon1 = PatientCoupon(
            patient_name="Patient 1",
            cpr="123456789",
            coupon_reference="CPN-DUP",
            quantity_pieces=10,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        self.session.add(coupon1)
        self.session.commit()
        
        coupon2 = PatientCoupon(
            patient_name="Patient 2",
            cpr="987654321",
            coupon_reference="CPN-DUP",
            quantity_pieces=5,
            medical_centre_id=self.centre.id,
            distribution_location_id=self.location.id,
            product_id=self.product.id
        )
        
        self.session.add(coupon2)
        with self.assertRaises(IntegrityError):
            self.session.commit()


if __name__ == '__main__':
    unittest.main(verbosity=2)
