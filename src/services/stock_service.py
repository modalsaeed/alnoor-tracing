"""
Stock Service - Business logic for stock management and calculations.

Handles stock tracking, updates, and calculations across purchase orders
and coupon verifications.
"""

from typing import List, Dict, Optional
from sqlalchemy import func

from database import (
    DatabaseManager,
    Product,
    PurchaseOrder,
    PatientCoupon,
)


class StockService:
    """Service for managing stock operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_total_stock_by_product(self, product_id: int) -> int:
        """
        Get total remaining stock for a product across all purchase orders.
        
        Args:
            product_id: The product ID
            
        Returns:
            Total remaining stock
        """
        with self.db_manager.get_session() as session:
            total = session.query(
                func.sum(PurchaseOrder.remaining_stock)
            ).filter(
                PurchaseOrder.product_id == product_id
            ).scalar()
            
            return total or 0
    
    def get_stock_summary(self) -> List[Dict]:
        """
        Get stock summary for all products.
        
        Returns:
            List of dictionaries with product and stock info
        """
        with self.db_manager.get_session() as session:
            products = session.query(Product).all()
            
            summary = []
            for product in products:
                total_ordered = session.query(
                    func.sum(PurchaseOrder.quantity)
                ).filter(
                    PurchaseOrder.product_id == product.id
                ).scalar() or 0
                
                total_remaining = session.query(
                    func.sum(PurchaseOrder.remaining_stock)
                ).filter(
                    PurchaseOrder.product_id == product.id
                ).scalar() or 0
                
                total_used = total_ordered - total_remaining
                
                summary.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_reference': product.reference,
                    'total_ordered': total_ordered,
                    'total_remaining': total_remaining,
                    'total_used': total_used,
                    'usage_percentage': (total_used / total_ordered * 100) if total_ordered > 0 else 0
                })
            
            return summary
    
    def deduct_stock(self, product_id: int, quantity: int) -> bool:
        """
        Deduct stock from purchase orders when coupon is verified.
        Uses FIFO (First In, First Out) approach.
        
        Args:
            product_id: The product ID
            quantity: Quantity to deduct
            
        Returns:
            True if successful, False if insufficient stock
        """
        with self.db_manager.get_session() as session:
            # Check if enough stock available
            total_stock = self.get_total_stock_by_product(product_id)
            if total_stock < quantity:
                return False
            
            # Get purchase orders with stock, ordered by creation date (FIFO)
            pos = session.query(PurchaseOrder).filter(
                PurchaseOrder.product_id == product_id,
                PurchaseOrder.remaining_stock > 0
            ).order_by(PurchaseOrder.created_at).all()
            
            remaining_to_deduct = quantity
            
            for po in pos:
                if remaining_to_deduct <= 0:
                    break
                
                if po.remaining_stock >= remaining_to_deduct:
                    # This PO has enough stock
                    po.remaining_stock -= remaining_to_deduct
                    remaining_to_deduct = 0
                else:
                    # Use all remaining stock from this PO
                    remaining_to_deduct -= po.remaining_stock
                    po.remaining_stock = 0
            
            session.commit()
            
            # Log the stock deduction
            self.db_manager.log_activity(
                'UPDATE',
                'purchase_orders',
                0,  # Multiple POs might be affected
                f'Deducted {quantity} units of product ID {product_id} from stock'
            )
            
            return True
    
    def restore_stock(self, product_id: int, quantity: int) -> bool:
        """
        Restore stock to purchase orders (e.g., when coupon is un-verified).
        Restores to the most recent PO first (reverse FIFO).
        
        Args:
            product_id: The product ID
            quantity: Quantity to restore
            
        Returns:
            True if successful
        """
        with self.db_manager.get_session() as session:
            # Get purchase orders for this product, ordered by creation date (newest first)
            pos = session.query(PurchaseOrder).filter(
                PurchaseOrder.product_id == product_id
            ).order_by(PurchaseOrder.created_at.desc()).all()
            
            if not pos:
                return False
            
            remaining_to_restore = quantity
            
            for po in pos:
                if remaining_to_restore <= 0:
                    break
                
                # Calculate how much we can restore to this PO
                max_restorable = po.quantity - po.remaining_stock
                
                if max_restorable >= remaining_to_restore:
                    # Can restore all to this PO
                    po.remaining_stock += remaining_to_restore
                    remaining_to_restore = 0
                else:
                    # Restore what we can to this PO
                    po.remaining_stock += max_restorable
                    remaining_to_restore -= max_restorable
            
            session.commit()
            
            # Log the stock restoration
            self.db_manager.log_activity(
                'UPDATE',
                'purchase_orders',
                0,
                f'Restored {quantity} units of product ID {product_id} to stock'
            )
            
            return True
    
    def get_low_stock_products(self, threshold_percentage: float = 20.0) -> List[Dict]:
        """
        Get products with low stock levels.
        
        Args:
            threshold_percentage: Alert threshold (default 20%)
            
        Returns:
            List of products with stock below threshold
        """
        summary = self.get_stock_summary()
        
        low_stock = [
            item for item in summary
            if item['total_ordered'] > 0 and
            (item['total_remaining'] / item['total_ordered'] * 100) <= threshold_percentage
        ]
        
        return low_stock
    
    def validate_stock_availability(self, product_id: int, quantity: int) -> tuple[bool, str]:
        """
        Validate if requested quantity is available in stock.
        
        Args:
            product_id: The product ID
            quantity: Requested quantity
            
        Returns:
            Tuple of (is_available, message)
        """
        available = self.get_total_stock_by_product(product_id)
        
        if available >= quantity:
            return True, f"Stock available: {available} units"
        else:
            return False, f"Insufficient stock. Available: {available}, Requested: {quantity}"
