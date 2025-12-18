"""
Database Migration Script for v1.0.2

Adds new columns to patient_coupons table:
- delivery_note_number
- grv_reference

Run this script once to upgrade existing databases.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from src.database.db_manager import DatabaseManager


def migrate_database():
    """Add new columns to patient_coupons table."""
    print("=" * 60)
    print("Alnoor Medical Services - Database Migration to v1.0.2")
    print("=" * 60)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    engine = db_manager._engine
    
    # Check if columns already exist
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('patient_coupons')]
    
    print(f"\nCurrent patient_coupons columns: {', '.join(columns)}")
    
    migrations_needed = []
    
    if 'delivery_note_number' not in columns:
        migrations_needed.append('delivery_note_number')
    
    if 'grv_reference' not in columns:
        migrations_needed.append('grv_reference')
    
    if not migrations_needed:
        print("\n✓ Database is already up to date!")
        print("  No migration needed.")
        return
    
    print(f"\nMigrations needed: {', '.join(migrations_needed)}")
    print("\nStarting migration...")
    
    try:
        with engine.begin() as connection:
            # Add delivery_note_number column if needed
            if 'delivery_note_number' in migrations_needed:
                print("  - Adding delivery_note_number column...")
                connection.execute(text(
                    "ALTER TABLE patient_coupons ADD COLUMN delivery_note_number VARCHAR(100)"
                ))
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_delivery_note_number ON patient_coupons(delivery_note_number)"
                ))
                print("    ✓ delivery_note_number column added")
            
            # Add grv_reference column if needed
            if 'grv_reference' in migrations_needed:
                print("  - Adding grv_reference column...")
                connection.execute(text(
                    "ALTER TABLE patient_coupons ADD COLUMN grv_reference VARCHAR(100)"
                ))
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_grv_reference ON patient_coupons(grv_reference)"
                ))
                print("    ✓ grv_reference column added")
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nNew features available:")
        print("  • Delivery Note tracking in coupon verification")
        print("  • GRV Reference management for verified bundles")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nPlease check the error and try again.")
        sys.exit(1)


if __name__ == "__main__":
    migrate_database()
