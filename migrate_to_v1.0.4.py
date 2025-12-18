"""
Database Migration Script: v1.0.3 -> v1.0.4
Changes:
1. Add 'unit' column to products table (nullable, max 50 chars)
2. Create new 'pharmacies' table with relationships
3. Add 'pharmacy_id' column to distribution_locations table (nullable FK to pharmacies)
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'alnoor.db')

def migrate():
    """Execute migration to v1.0.4"""
    print(f"Starting migration to v1.0.4...")
    print(f"Database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        print("\n1. Adding 'unit' column to products table...")
        cursor.execute("""
            ALTER TABLE products 
            ADD COLUMN unit VARCHAR(50)
        """)
        print("   ✓ 'unit' column added to products")
        
        print("\n2. Creating 'pharmacies' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pharmacies (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                reference VARCHAR(50) NOT NULL UNIQUE,
                contact_person VARCHAR(100),
                phone VARCHAR(20),
                email VARCHAR(100),
                notes TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on reference
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_pharmacies_reference 
            ON pharmacies (reference)
        """)
        print("   ✓ 'pharmacies' table created")
        print("   ✓ Index on 'reference' created")
        
        print("\n3. Adding 'pharmacy_id' column to distribution_locations table...")
        cursor.execute("""
            ALTER TABLE distribution_locations 
            ADD COLUMN pharmacy_id INTEGER REFERENCES pharmacies(id)
        """)
        print("   ✓ 'pharmacy_id' column added to distribution_locations")
        
        # Commit transaction
        conn.commit()
        print("\n✅ Migration to v1.0.4 completed successfully!")
        
        # Verify changes
        print("\nVerifying changes...")
        cursor.execute("PRAGMA table_info(products)")
        products_cols = [col[1] for col in cursor.fetchall()]
        print(f"   Products columns: {products_cols}")
        
        cursor.execute("PRAGMA table_info(pharmacies)")
        pharmacy_cols = [col[1] for col in cursor.fetchall()]
        print(f"   Pharmacies columns: {pharmacy_cols}")
        
        cursor.execute("PRAGMA table_info(distribution_locations)")
        dist_cols = [col[1] for col in cursor.fetchall()]
        print(f"   Distribution locations columns: {dist_cols}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("Database Migration: v1.0.3 -> v1.0.4")
    print("="*60)
    
    backup_msg = """
⚠️  IMPORTANT: This will modify your database schema.
   A backup is recommended before proceeding.
   
Continue with migration? (yes/no): """
    
    response = input(backup_msg).strip().lower()
    
    if response in ['yes', 'y']:
        success = migrate()
        if success:
            print("\n" + "="*60)
            print("Migration completed! You can now run the application.")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("Migration failed. Please check the error messages above.")
            print("="*60)
    else:
        print("\nMigration cancelled.")
