"""
Tests for Stock Service.

Tests the stock management business logic including:
- Stock calculations
- FIFO deduction logic
- Stock restoration
- Low stock alerts
- Stock validation
"""

import pytest
from datetime import datetime, timedelta

from database import DatabaseManager, Product, PurchaseOrder, PatientCoupon
from services import StockService


@pytest.fixture
def db_manager(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_stock.db"
    manager = DatabaseManager(str(db_path))
    manager.init_db()
    yield manager
    manager.close()


@pytest.fixture
def stock_service(db_manager):
    """Create a stock service instance."""
    return StockService(db_manager)


@pytest.fixture
def sample_products(db_manager):
    """Create sample products for testing."""
    products = [
        Product(reference="PROD001", name="Paracetamol 500mg", description="Pain relief"),
        Product(reference="PROD002", name="Amoxicillin 250mg", description="Antibiotic"),
        Product(reference="PROD003", name="Vitamin D3", description="Supplement"),
    ]
    
    with db_manager.get_session() as session:
        for product in products:
            session.add(product)
        session.commit()
        
        # Refresh to get IDs
        for product in products:
            session.refresh(product)
    
    return products


@pytest.fixture
def sample_purchase_orders(db_manager, sample_products):
    """Create sample purchase orders for testing."""
    now = datetime.now()
    
    purchase_orders = [
        # Product 1 - Multiple POs for FIFO testing
        PurchaseOrder(
            reference="PO001",
            product_id=sample_products[0].id,
            quantity=100,
            remaining_stock=100,
            created_at=now - timedelta(days=30)  # Oldest
        ),
        PurchaseOrder(
            reference="PO002",
            product_id=sample_products[0].id,
            quantity=50,
            remaining_stock=50,
            created_at=now - timedelta(days=20)  # Middle
        ),
        PurchaseOrder(
            reference="PO003",
            product_id=sample_products[0].id,
            quantity=75,
            remaining_stock=75,
            created_at=now - timedelta(days=10)  # Newest
        ),
        
        # Product 2 - Single PO
        PurchaseOrder(
            reference="PO004",
            product_id=sample_products[1].id,
            quantity=200,
            remaining_stock=200,
            created_at=now - timedelta(days=15)
        ),
        
        # Product 3 - Low stock PO
        PurchaseOrder(
            reference="PO005",
            product_id=sample_products[2].id,
            quantity=100,
            remaining_stock=10,  # Only 10% remaining
            created_at=now - timedelta(days=25)
        ),
    ]
    
    with db_manager.get_session() as session:
        for po in purchase_orders:
            session.add(po)
        session.commit()
        
        for po in purchase_orders:
            session.refresh(po)
    
    return purchase_orders


class TestStockCalculations:
    """Test stock calculation methods."""
    
    def test_get_total_stock_single_po(self, stock_service, sample_purchase_orders, sample_products):
        """Test getting total stock for product with single PO."""
        total = stock_service.get_total_stock_by_product(sample_products[1].id)
        assert total == 200
    
    def test_get_total_stock_multiple_pos(self, stock_service, sample_purchase_orders, sample_products):
        """Test getting total stock for product with multiple POs."""
        total = stock_service.get_total_stock_by_product(sample_products[0].id)
        assert total == 225  # 100 + 50 + 75
    
    def test_get_total_stock_no_pos(self, stock_service, db_manager):
        """Test getting total stock for product with no POs."""
        # Create product without POs
        product = Product(reference="NOSTOCK", name="No Stock Product", description="Test")
        with db_manager.get_session() as session:
            session.add(product)
            session.commit()
            session.refresh(product)
        
        total = stock_service.get_total_stock_by_product(product.id)
        assert total == 0
    
    def test_get_stock_summary(self, stock_service, sample_purchase_orders, sample_products):
        """Test getting stock summary for all products."""
        summary = stock_service.get_stock_summary()
        
        assert len(summary) == 3
        
        # Check product 1 (multiple POs)
        prod1_summary = next(s for s in summary if s['product_id'] == sample_products[0].id)
        assert prod1_summary['total_ordered'] == 225  # 100 + 50 + 75
        assert prod1_summary['total_remaining'] == 225
        assert prod1_summary['total_used'] == 0
        assert prod1_summary['usage_percentage'] == 0
        
        # Check product 3 (low stock)
        prod3_summary = next(s for s in summary if s['product_id'] == sample_products[2].id)
        assert prod3_summary['total_ordered'] == 100
        assert prod3_summary['total_remaining'] == 10
        assert prod3_summary['total_used'] == 90
        assert prod3_summary['usage_percentage'] == 90


class TestFIFOStockDeduction:
    """Test FIFO (First In, First Out) stock deduction logic."""
    
    def test_deduct_from_single_po(self, stock_service, db_manager, sample_purchase_orders, sample_products):
        """Test deducting stock from a single PO."""
        product_id = sample_products[1].id
        
        # Deduct 50 units
        result = stock_service.deduct_stock(product_id, 50)
        assert result is True
        
        # Check remaining stock
        total = stock_service.get_total_stock_by_product(product_id)
        assert total == 150  # 200 - 50
    
    def test_deduct_exact_po_amount(self, stock_service, db_manager, sample_purchase_orders, sample_products):
        """Test deducting exact amount from a PO (should empty it)."""
        product_id = sample_products[1].id
        
        # Deduct entire PO
        result = stock_service.deduct_stock(product_id, 200)
        assert result is True
        
        # Check remaining stock
        total = stock_service.get_total_stock_by_product(product_id)
        assert total == 0
    
    def test_deduct_across_multiple_pos_fifo(self, stock_service, db_manager, sample_purchase_orders, sample_products):
        """Test that deduction follows FIFO (oldest PO first)."""
        product_id = sample_products[0].id
        
        # Deduct 120 units (should take all 100 from PO001 and 20 from PO002)
        result = stock_service.deduct_stock(product_id, 120)
        assert result is True
        
        # Check each PO
        with db_manager.get_session() as session:
            po001 = session.query(PurchaseOrder).filter_by(reference="PO001").first()
            po002 = session.query(PurchaseOrder).filter_by(reference="PO002").first()
            po003 = session.query(PurchaseOrder).filter_by(reference="PO003").first()
            
            assert po001.remaining_stock == 0    # Fully depleted (oldest)
            assert po002.remaining_stock == 30   # Partially used (50 - 20)
            assert po003.remaining_stock == 75   # Untouched (newest)
    
    def test_deduct_all_stock_across_pos(self, stock_service, db_manager, sample_purchase_orders, sample_products):
        """Test deducting all stock across multiple POs."""
        product_id = sample_products[0].id
        
        # Deduct all 225 units
        result = stock_service.deduct_stock(product_id, 225)
        assert result is True
        
        # Check total is zero
        total = stock_service.get_total_stock_by_product(product_id)
        assert total == 0
        
        # Check all POs are empty
        with db_manager.get_session() as session:
            pos = session.query(PurchaseOrder).filter_by(product_id=product_id).all()
            for po in pos:
                assert po.remaining_stock == 0
    
    def test_deduct_insufficient_stock(self, stock_service, sample_purchase_orders, sample_products):
        """Test that deduction fails when insufficient stock."""
        product_id = sample_products[0].id
        
        # Try to deduct more than available (225 available, try 300)
        result = stock_service.deduct_stock(product_id, 300)
        assert result is False
        
        # Check stock unchanged
        total = stock_service.get_total_stock_by_product(product_id)
        assert total == 225
    
    def test_deduct_zero_units(self, stock_service, sample_purchase_orders, sample_products):
        """Test deducting zero units (should succeed but do nothing)."""
        product_id = sample_products[0].id
        
        result = stock_service.deduct_stock(product_id, 0)
        assert result is True
        
        # Check stock unchanged
        total = stock_service.get_total_stock_by_product(product_id)
        assert total == 225


class TestStockRestoration:
    """Test stock restoration logic (reverse FIFO)."""
    
    def test_restore_to_most_recent_po(self, stock_service, db_manager, sample_purchase_orders, sample_products):
        """Test that restoration goes to most recent PO first."""
        product_id = sample_products[0].id
        
        # First, deduct some stock
        stock_service.deduct_stock(product_id, 120)  # Empties PO001, reduces PO002
        
        # Now restore 50 units (should go to PO003 - most recent)
        result = stock_service.restore_stock(product_id, 50)
        assert result is True
        
        with db_manager.get_session() as session:
            po001 = session.query(PurchaseOrder).filter_by(reference="PO001").first()
            po002 = session.query(PurchaseOrder).filter_by(reference="PO002").first()
            po003 = session.query(PurchaseOrder).filter_by(reference="PO003").first()
            
            assert po001.remaining_stock == 0    # Still empty
            assert po002.remaining_stock == 30   # Still 30 (50 - 20 from deduction)
            assert po003.remaining_stock == 125  # 75 + 50 restored
    
    def test_restore_across_multiple_pos(self, stock_service, db_manager, sample_purchase_orders, sample_products):
        """Test restoration across multiple POs."""
        product_id = sample_products[0].id
        
        # Deduct all stock
        stock_service.deduct_stock(product_id, 225)
        
        # Restore 100 units (should fill PO003 fully, then start on PO002)
        result = stock_service.restore_stock(product_id, 100)
        assert result is True
        
        with db_manager.get_session() as session:
            po001 = session.query(PurchaseOrder).filter_by(reference="PO001").first()
            po002 = session.query(PurchaseOrder).filter_by(reference="PO002").first()
            po003 = session.query(PurchaseOrder).filter_by(reference="PO003").first()
            
            assert po001.remaining_stock == 0   # Still empty
            assert po002.remaining_stock == 25  # 25 restored (100 - 75 for PO003)
            assert po003.remaining_stock == 75  # Fully restored
    
    def test_restore_respects_po_limits(self, stock_service, db_manager, sample_purchase_orders, sample_products):
        """Test that restoration doesn't exceed PO original quantity."""
        product_id = sample_products[1].id  # Single PO with 200 units
        
        # Deduct 100 units
        stock_service.deduct_stock(product_id, 100)
        
        # Try to restore 150 units (should only restore 100)
        result = stock_service.restore_stock(product_id, 150)
        assert result is True
        
        # Check total is back to 200 (not 250)
        total = stock_service.get_total_stock_by_product(product_id)
        assert total == 200


class TestLowStockAlerts:
    """Test low stock detection."""
    
    def test_get_low_stock_products_default_threshold(self, stock_service, sample_purchase_orders, sample_products):
        """Test getting low stock products with default 20% threshold."""
        low_stock = stock_service.get_low_stock_products()
        
        # Product 3 has 10% remaining (10/100), should be flagged
        assert len(low_stock) == 1
        assert low_stock[0]['product_id'] == sample_products[2].id
        assert low_stock[0]['total_remaining'] == 10
    
    def test_get_low_stock_custom_threshold(self, stock_service, sample_purchase_orders, sample_products):
        """Test getting low stock products with custom threshold."""
        # Set threshold to 50% - should catch product 3 (10%)
        low_stock = stock_service.get_low_stock_products(threshold_percentage=50.0)
        
        assert len(low_stock) == 1
        assert low_stock[0]['product_id'] == sample_products[2].id
    
    def test_no_low_stock_products(self, stock_service, sample_purchase_orders, sample_products):
        """Test when no products are low on stock."""
        # Set threshold very low (5%) - product 3 has 10%, so shouldn't be flagged
        low_stock = stock_service.get_low_stock_products(threshold_percentage=5.0)
        
        assert len(low_stock) == 0
    
    def test_low_stock_after_deduction(self, stock_service, sample_purchase_orders, sample_products):
        """Test low stock detection after deducting stock."""
        product_id = sample_products[1].id
        
        # Initially not low (200/200 = 100%)
        low_stock = stock_service.get_low_stock_products()
        assert all(item['product_id'] != product_id for item in low_stock)
        
        # Deduct stock to bring below 20% (deduct 170, leaving 30/200 = 15%)
        stock_service.deduct_stock(product_id, 170)
        
        # Should now be flagged
        low_stock = stock_service.get_low_stock_products()
        assert any(item['product_id'] == product_id for item in low_stock)


class TestStockValidation:
    """Test stock availability validation."""
    
    def test_validate_sufficient_stock(self, stock_service, sample_purchase_orders, sample_products):
        """Test validation passes when stock is sufficient."""
        product_id = sample_products[0].id
        
        is_available, message = stock_service.validate_stock_availability(product_id, 100)
        
        assert is_available is True
        assert "225" in message  # Should mention available stock
    
    def test_validate_exact_stock(self, stock_service, sample_purchase_orders, sample_products):
        """Test validation passes when requesting exact available stock."""
        product_id = sample_products[0].id
        
        is_available, message = stock_service.validate_stock_availability(product_id, 225)
        
        assert is_available is True
    
    def test_validate_insufficient_stock(self, stock_service, sample_purchase_orders, sample_products):
        """Test validation fails when stock is insufficient."""
        product_id = sample_products[0].id
        
        is_available, message = stock_service.validate_stock_availability(product_id, 300)
        
        assert is_available is False
        assert "Insufficient" in message
        assert "225" in message  # Should mention available
        assert "300" in message  # Should mention requested
    
    def test_validate_zero_stock(self, stock_service, db_manager):
        """Test validation with product that has no stock."""
        # Create product without POs
        product = Product(reference="ZERO", name="Zero Stock", description="Test")
        with db_manager.get_session() as session:
            session.add(product)
            session.commit()
            session.refresh(product)
        
        is_available, message = stock_service.validate_stock_availability(product.id, 1)
        
        assert is_available is False
        assert "0" in message


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_coupon_verification_workflow(self, stock_service, db_manager, sample_purchase_orders, sample_products):
        """Test stock deduction when verifying a coupon."""
        product_id = sample_products[0].id
        quantity = 10
        
        # Initial stock
        initial_stock = stock_service.get_total_stock_by_product(product_id)
        assert initial_stock == 225
        
        # Verify coupon (deduct stock)
        result = stock_service.deduct_stock(product_id, quantity)
        assert result is True
        
        # Check stock reduced
        new_stock = stock_service.get_total_stock_by_product(product_id)
        assert new_stock == 215  # 225 - 10
        
        # Unverify coupon (restore stock)
        result = stock_service.restore_stock(product_id, quantity)
        assert result is True
        
        # Check stock restored
        final_stock = stock_service.get_total_stock_by_product(product_id)
        assert final_stock == 225
    
    def test_multiple_coupons_deplete_stock(self, stock_service, sample_purchase_orders, sample_products):
        """Test multiple coupon verifications depleting stock."""
        product_id = sample_products[2].id  # Product with only 10 remaining
        
        # Verify first coupon (5 units)
        result1 = stock_service.deduct_stock(product_id, 5)
        assert result1 is True
        assert stock_service.get_total_stock_by_product(product_id) == 5
        
        # Verify second coupon (5 units)
        result2 = stock_service.deduct_stock(product_id, 5)
        assert result2 is True
        assert stock_service.get_total_stock_by_product(product_id) == 0
        
        # Try third coupon (should fail - no stock)
        result3 = stock_service.deduct_stock(product_id, 1)
        assert result3 is False
        assert stock_service.get_total_stock_by_product(product_id) == 0
    
    def test_concurrent_deductions_same_product(self, stock_service, sample_purchase_orders, sample_products):
        """Test multiple deductions from the same product."""
        product_id = sample_products[0].id
        
        # Multiple deductions
        stock_service.deduct_stock(product_id, 50)
        stock_service.deduct_stock(product_id, 75)
        stock_service.deduct_stock(product_id, 30)
        
        # Check total deducted correctly
        remaining = stock_service.get_total_stock_by_product(product_id)
        assert remaining == 70  # 225 - 50 - 75 - 30
