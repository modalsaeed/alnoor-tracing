"""
Database Migration Script for v1.0.3

Major Changes:
1. Creates new 'purchases' table for supplier invoices
2. Updates transactions table to reference purchases instead of purchase_orders
3. Adds stock flow: Local PO -> Purchase -> Transaction -> Coupon

IMPORTANT: This migration will:
- Create the new purchases table
- Alter transactions table (drops purchase_order_id, adds purchase_id)
- Existing transaction data will be LOST unless manually migrated
- Make sure to backup your database before running this migration

Run this script once to upgrade from v1.0.2 to v1.0.3
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from src.database.db_manager import DatabaseManager


def migrate_database():
    """Perform database migration for v1.0.3"""
    print("=" * 70)
    print("Alnoor Medical Services - Database Migration to v1.0.3")
    print("=" * 70)
    print("\n⚠️  WARNING: This migration will restructure the transactions table!")
    print("   Existing transaction data may be lost.")
    print("   Please ensure you have backed up your database.\n")
    
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\nMigration cancelled.")
        return
    
    # Initialize database manager
    db_manager = DatabaseManager()
    engine = db_manager._engine
    
    # Check existing tables
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"\nExisting tables: {', '.join(existing_tables)}")
    
    migrations_needed = []
    
    # Check if purchases table exists
    if 'purchases' not in existing_tables:
        migrations_needed.append('create_purchases_table')
    
    # Check if transactions table needs update
    if 'transactions' in existing_tables:
        columns = [col['name'] for col in inspector.get_columns('transactions')]
        if 'purchase_order_id' in columns and 'purchase_id' not in columns:
            migrations_needed.append('update_transactions_table')
    
    if not migrations_needed:
        print("\n✓ Database is already up to date!")
        print("  No migration needed.")
        return
    
    print(f"\nMigrations needed: {', '.join(migrations_needed)}")
    print("\nStarting migration...")
    
    try:
        with engine.begin() as connection:
            # Step 1: Create purchases table
            if 'create_purchases_table' in migrations_needed:
                print("\n  [1/2] Creating 'purchases' table...")
                connection.execute(text("""
                    CREATE TABLE purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_number VARCHAR(100) NOT NULL UNIQUE,
                        purchase_order_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL,
                        remaining_stock INTEGER NOT NULL,
                        unit_price NUMERIC(10, 3) NOT NULL,
                        total_price NUMERIC(10, 3) NOT NULL,
                        purchase_date DATETIME NOT NULL,
                        supplier_name VARCHAR(255),
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
                        FOREIGN KEY (product_id) REFERENCES products(id),
                        CHECK (quantity > 0),
                        CHECK (remaining_stock >= 0),
                        CHECK (remaining_stock <= quantity),
                        CHECK (unit_price >= 0),
                        CHECK (total_price >= 0)
                    )
                """))
                
                # Create indexes
                connection.execute(text(
                    "CREATE INDEX idx_purchases_invoice_number ON purchases(invoice_number)"
                ))
                connection.execute(text(
                    "CREATE INDEX idx_purchases_purchase_date ON purchases(purchase_date)"
                ))
                
                print("    ✓ 'purchases' table created")
            
            # Step 2: Update transactions table
            if 'update_transactions_table' in migrations_needed:
                print("\n  [2/2] Updating 'transactions' table structure...")
                
                # Check if there are existing transactions
                result = connection.execute(text("SELECT COUNT(*) FROM transactions"))
                transaction_count = result.scalar()
                
                if transaction_count > 0:
                    print(f"    ⚠️  Found {transaction_count} existing transaction(s)")
                    print("    These will be temporarily backed up...")
                    
                    # Backup existing transactions
                    connection.execute(text("""
                        CREATE TABLE transactions_backup AS 
                        SELECT * FROM transactions
                    """))
                    print("    ✓ Backup created: transactions_backup")
                
                # Drop old transactions table
                connection.execute(text("DROP TABLE transactions"))
                
                # Create new transactions table with purchase_id
                connection.execute(text("""
                    CREATE TABLE transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transaction_reference VARCHAR(100) NOT NULL UNIQUE,
                        purchase_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        distribution_location_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL,
                        transaction_date DATETIME NOT NULL,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (purchase_id) REFERENCES purchases(id),
                        FOREIGN KEY (product_id) REFERENCES products(id),
                        FOREIGN KEY (distribution_location_id) REFERENCES distribution_locations(id),
                        CHECK (quantity > 0)
                    )
                """))
                
                # Create indexes
                connection.execute(text(
                    "CREATE INDEX idx_transactions_reference ON transactions(transaction_reference)"
                ))
                connection.execute(text(
                    "CREATE INDEX idx_transactions_date ON transactions(transaction_date)"
                ))
                
                print("    ✓ 'transactions' table updated")
                
                if transaction_count > 0:
                    print(f"\n    ℹ️  Note: {transaction_count} transaction(s) backed up to 'transactions_backup'")
                    print("    You will need to manually migrate them to the new structure:")
                    print("    1. Create Purchase records for each old transaction")
                    print("    2. Link new transactions to those purchases")
                    print("    3. Drop the transactions_backup table when done")
        
        print("\n" + "=" * 70)
        print("✓ Migration completed successfully!")
        print("=" * 70)
        print("\nNew stock flow is now active:")
        print("  Local PO → Purchase (Supplier Invoice) → Transaction → Coupon")
        print("\nNew features:")
        print("  • Purchases table to track supplier invoices")
        print("  • Track which specific purchase batch goes to each location")
        print("  • Better inventory management with purchase-level tracking")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nPlease check the error and try again.")
        print("If you have backup data, you can restore it manually.")
        sys.exit(1)


if __name__ == "__main__":
    migrate_database()
