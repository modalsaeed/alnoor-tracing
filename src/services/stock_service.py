"""
Stock Service - Business logic for stock management and calculations.

Handles stock tracking, updates, and calculations across purchase orders
and transactions. Stock is now managed through the Transaction table
when products are transferred to distribution locations.
"""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import func

from src.database.db_manager import DatabaseManager
from src.database.models import (
    Product,
    PurchaseOrder,
    PatientCoupon,
    Transaction,
    DistributionLocation,
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
        [DEPRECATED] Deduct stock from purchase orders when coupon is verified.
        
        IMPORTANT: This method is deprecated. Use create_transaction() instead.
        Stock should now be managed through the Transaction table when products
        are transferred to distribution locations, not during coupon verification.
        
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
    
    # ==================== NEW TRANSACTION-BASED METHODS ====================
    
    def create_transaction(
        self, 
        transaction_reference: str,
        purchase_order_id: int,
        product_id: int,
        distribution_location_id: int,
        quantity: int,
        transaction_date: Optional[datetime] = None
    ) -> tuple[bool, str, Optional[Transaction]]:
        """
        Create a transaction and deduct stock using FIFO from purchase orders.
        
        This is the NEW recommended method for stock management. Use this when
        products are transferred to distribution locations.
        
        Args:
            transaction_reference: Unique reference for this transaction
            purchase_order_id: Purchase order this transaction is linked to
            product_id: The product being transferred
            distribution_location_id: Destination distribution location
            quantity: Quantity being transferred
            transaction_date: Date of transaction (defaults to now)
            
        Returns:
            Tuple of (success, message, transaction_object)
        """
        try:
            with self.db_manager.get_session() as session:
                # Validate stock availability
                total_stock = self.get_total_stock_by_product(product_id)
                if total_stock < quantity:
                    return False, f"Insufficient stock. Available: {total_stock}, Requested: {quantity}", None
                
                # Validate purchase order exists and has the correct product
                po = session.query(PurchaseOrder).get(purchase_order_id)
                if not po:
                    return False, f"Purchase order ID {purchase_order_id} not found", None
                
                if po.product_id != product_id:
                    return False, f"Purchase order product mismatch. PO has product {po.product_id}, requested {product_id}", None
                
                # Deduct stock using FIFO
                deduction_success = self._deduct_stock_fifo(session, product_id, quantity)
                if not deduction_success:
                    return False, f"Failed to deduct stock using FIFO", None
                
                # Create transaction record
                transaction = Transaction(
                    transaction_reference=transaction_reference.upper(),
                    purchase_order_id=purchase_order_id,
                    product_id=product_id,
                    distribution_location_id=distribution_location_id,
                    quantity=quantity,
                    transaction_date=transaction_date or datetime.now()
                )
                
                session.add(transaction)
                session.commit()
                
                # Refresh to get relationships
                session.refresh(transaction)
                
                # Log the transaction
                self.db_manager.log_activity(
                    'CREATE',
                    'transactions',
                    transaction.id,
                    f'Created transaction {transaction_reference}: {quantity} units of product ID {product_id} to location ID {distribution_location_id}'
                )
                
                return True, f"Transaction created successfully. Stock deducted: {quantity} units", transaction
                
        except Exception as e:
            return False, f"Error creating transaction: {str(e)}", None
    
    def _deduct_stock_fifo(self, session, product_id: int, quantity: int) -> bool:
        """
        Internal method to deduct stock using FIFO within an existing session.
        
        Args:
            session: Active SQLAlchemy session
            product_id: The product ID
            quantity: Quantity to deduct
            
        Returns:
            True if successful, False otherwise
        """
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
        
        return remaining_to_deduct == 0
    
    def get_transactions_by_product(self, product_id: int) -> List[Transaction]:
        """
        Get all transactions for a specific product.
        
        Args:
            product_id: The product ID
            
        Returns:
            List of Transaction objects
        """
        with self.db_manager.get_session() as session:
            transactions = session.query(Transaction).filter(
                Transaction.product_id == product_id
            ).order_by(Transaction.transaction_date.desc()).all()
            
            return transactions
    
    def get_transactions_by_location(self, location_id: int) -> List[Transaction]:
        """
        Get all transactions for a specific distribution location.
        
        Args:
            location_id: The distribution location ID
            
        Returns:
            List of Transaction objects
        """
        with self.db_manager.get_session() as session:
            transactions = session.query(Transaction).filter(
                Transaction.distribution_location_id == location_id
            ).order_by(Transaction.transaction_date.desc()).all()
            
            return transactions
    
    def get_transaction_summary(self) -> List[Dict]:
        """
        Get summary of all transactions grouped by product.
        
        Returns:
            List of dictionaries with transaction summaries
        """
        with self.db_manager.get_session() as session:
            products = session.query(Product).all()
            
            summary = []
            for product in products:
                total_transferred = session.query(
                    func.sum(Transaction.quantity)
                ).filter(
                    Transaction.product_id == product.id
                ).scalar() or 0
                
                transaction_count = session.query(
                    func.count(Transaction.id)
                ).filter(
                    Transaction.product_id == product.id
                ).scalar() or 0
                
                summary.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_reference': product.reference,
                    'total_transferred': total_transferred,
                    'transaction_count': transaction_count
                })
            
            return summary
    
    def validate_transaction(
        self,
        product_id: int,
        quantity: int,
        purchase_order_id: int
    ) -> tuple[bool, str]:
        """
        Validate if a transaction can be created.
        
        Args:
            product_id: The product ID
            quantity: Requested quantity
            purchase_order_id: Purchase order ID
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check stock availability
        available = self.get_total_stock_by_product(product_id)
        if available < quantity:
            return False, f"Insufficient stock. Available: {available}, Requested: {quantity}"
        
        # Check purchase order exists
        with self.db_manager.get_session() as session:
            po = session.query(PurchaseOrder).get(purchase_order_id)
            if not po:
                return False, f"Purchase order ID {purchase_order_id} not found"
            
            if po.product_id != product_id:
                return False, f"Purchase order is for a different product"
        
        return True, "Transaction can be created"

