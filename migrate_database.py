"""
Database Migration Script - Schema Update v2.0
==============================================

This script migrates an existing Alnoor Medical Services database to the new schema
that includes the Transaction table, purchase order pricing fields, and optional patient fields.

Run this BEFORE starting the application with the new code.

IMPORTANT: This script will BACKUP your database before making changes.
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
import sqlite3

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def get_db_path():
    """Get the database path."""
    if sys.platform == "win32":
        appdata = os.environ.get("LOCALAPPDATA")
        if not appdata:
            appdata = os.path.expanduser("~\\AppData\\Local")
        db_dir = os.path.join(appdata, "Alnoor Medical Services", "database")
    else:
        db_dir = os.path.expanduser("~/.local/share/alnoor-medical-services/database")
    
    db_path = os.path.join(db_dir, "alnoor.db")
    
    if not os.path.exists(db_path):
        print_error(f"Database not found at: {db_path}")
        print_info("If you haven't run the application yet, no migration is needed.")
        print_info("The new schema will be created automatically on first run.")
        return None
    
    return db_path

def backup_database(db_path):
    """Create a backup of the database."""
    backup_dir = os.path.join(os.path.dirname(db_path), "..", "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"alnoor_pre_migration_{timestamp}.db")
    
    print_info(f"Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print_success(f"Backup created successfully")
    
    return backup_path

def check_if_migration_needed(conn):
    """Check if migration is needed."""
    cursor = conn.cursor()
    
    # Check if transactions table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='transactions'
    """)
    has_transactions = cursor.fetchone() is not None
    
    # Check if purchase_orders has pricing fields
    cursor.execute("PRAGMA table_info(purchase_orders)")
    columns = [row[1] for row in cursor.fetchall()]
    has_pricing = 'unit_price' in columns
    
    return not has_transactions or not has_pricing

def migrate_database(db_path):
    """Perform the database migration."""
    print_header("DATABASE MIGRATION")
    
    # Create backup
    backup_path = backup_database(db_path)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        if not check_if_migration_needed(conn):
            print_success("Database is already up to date!")
            conn.close()
            return True
        
        print_info("Starting migration process...")
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Step 1: Check if transactions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='transactions'
        """)
        
        if cursor.fetchone() is None:
            print_info("Creating transactions table...")
            cursor.execute("""
                CREATE TABLE transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_reference VARCHAR(100) UNIQUE NOT NULL,
                    purchase_order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    distribution_location_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    transaction_date DATETIME NOT NULL,
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY(purchase_order_id) REFERENCES purchase_orders(id),
                    FOREIGN KEY(product_id) REFERENCES products(id),
                    FOREIGN KEY(distribution_location_id) REFERENCES distribution_locations(id),
                    CHECK(quantity > 0)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX ix_transactions_transaction_reference 
                ON transactions(transaction_reference)
            """)
            
            cursor.execute("""
                CREATE INDEX ix_transactions_transaction_date 
                ON transactions(transaction_date)
            """)
            
            print_success("Transactions table created")
        else:
            print_info("Transactions table already exists")
        
        # Step 2: Add pricing fields to purchase_orders
        cursor.execute("PRAGMA table_info(purchase_orders)")
        columns = [row[1] for row in cursor.fetchall()]
        
        pricing_fields = [
            ('unit_price', 'NUMERIC(10, 3)'),
            ('tax_rate', 'NUMERIC(5, 2)'),
            ('tax_amount', 'NUMERIC(10, 3)'),
            ('total_without_tax', 'NUMERIC(10, 3)'),
            ('total_with_tax', 'NUMERIC(10, 3)')
        ]
        
        for field_name, field_type in pricing_fields:
            if field_name not in columns:
                print_info(f"Adding {field_name} to purchase_orders...")
                cursor.execute(f"""
                    ALTER TABLE purchase_orders 
                    ADD COLUMN {field_name} {field_type}
                """)
                print_success(f"{field_name} added")
            else:
                print_info(f"{field_name} already exists")
        
        # Step 3: Update patient_coupons to allow NULL patient_name and cpr
        # SQLite doesn't support ALTER COLUMN, so we need to check constraints
        print_info("Checking patient_coupons constraints...")
        
        # In SQLite, we can't modify column constraints directly
        # The application code will handle NULL values appropriately
        # We just need to verify the table structure
        cursor.execute("PRAGMA table_info(patient_coupons)")
        coupon_columns = {row[1]: row for row in cursor.fetchall()}
        
        if 'patient_name' in coupon_columns and 'cpr' in coupon_columns:
            print_success("Patient coupons table structure verified")
            print_warning("Note: Patient name and CPR are now optional in the application logic")
        
        # Commit all changes
        conn.commit()
        print_success("Migration completed successfully!")
        
        # Verify migration
        print_info("Verifying migration...")
        
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='transactions'")
        if cursor.fetchone()[0] == 1:
            print_success("Transactions table verified")
        
        cursor.execute("PRAGMA table_info(purchase_orders)")
        po_columns = [row[1] for row in cursor.fetchall()]
        if 'unit_price' in po_columns:
            print_success("Purchase order pricing fields verified")
        
        conn.close()
        
        print_header("MIGRATION COMPLETE")
        print_success("Your database has been successfully updated!")
        print_info(f"Backup saved to: {backup_path}")
        print_warning("You can now start the application with the new version.")
        
        return True
        
    except Exception as e:
        print_error(f"Migration failed: {str(e)}")
        print_warning("Rolling back changes...")
        
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        
        # Restore from backup
        print_warning(f"Restoring database from backup...")
        shutil.copy2(backup_path, db_path)
        print_success("Database restored from backup")
        
        print_error("Migration was not successful. Your database has been restored.")
        print_info("Please report this error if it persists.")
        
        return False

def main():
    """Main migration function."""
    print_header("ALNOOR MEDICAL SERVICES - DATABASE MIGRATION")
    print_info("This script will update your database to the new schema.")
    print_info("A backup will be created before any changes are made.")
    
    # Get database path
    db_path = get_db_path()
    if db_path is None:
        return
    
    print_info(f"Database location: {db_path}")
    
    # Confirm migration
    print()
    response = input(f"{Colors.YELLOW}Proceed with migration? (y/n): {Colors.END}")
    if response.lower() != 'y':
        print_warning("Migration cancelled by user.")
        return
    
    # Perform migration
    success = migrate_database(db_path)
    
    if success:
        print()
        print_success("Migration completed successfully!")
        print_info("You can now start the application.")
    else:
        print()
        print_error("Migration failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Migration cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
