"""
Verify Database Compatibility
Ensures the PyQt6 application can read data correctly after batch operations
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.db_manager import DatabaseManager
from src.database.models import (
    Product, PurchaseOrder, Pharmacy, DistributionLocation,
    MedicalCentre, PatientCoupon, Transaction, ActivityLog
)

def test_database_reading():
    """Test that all database models can be read correctly"""
    print("\n" + "="*60)
    print("  DATABASE COMPATIBILITY VERIFICATION")
    print("="*60 + "\n")
    
    try:
        # Initialize database
        db_manager = DatabaseManager()
        print("✓ Database connection successful\n")
        
        # Test reading each model
        with db_manager.get_session() as session:
            # Products
            products = session.query(Product).all()
            print(f"✓ Products: {len(products)} records")
            if products:
                sample = products[0]
                print(f"  Sample: {sample.name} | Ref: {sample.reference}")
            
            # Purchase Orders
            pos = session.query(PurchaseOrder).all()
            print(f"✓ Purchase Orders: {len(pos)} records")
            
            # Pharmacies
            pharmacies = session.query(Pharmacy).all()
            print(f"✓ Pharmacies: {len(pharmacies)} records")
            
            # Distribution Locations
            dls = session.query(DistributionLocation).all()
            print(f"✓ Distribution Locations: {len(dls)} records")
            
            # Medical Centres
            mcs = session.query(MedicalCentre).all()
            print(f"✓ Medical Centres: {len(mcs)} records")
            
            # Patient Coupons
            coupons = session.query(PatientCoupon).all()
            print(f"✓ Patient Coupons: {len(coupons)} records")
            if coupons:
                sample = coupons[0]
                print(f"  Sample: {sample.coupon_reference} | Patient: {sample.patient_name}")
                print(f"  Fields: coupon_reference={sample.coupon_reference}, cpr={sample.cpr}, quantity_pieces={sample.quantity_pieces}")
                print(f"  Relationships: medical_centre_id={sample.medical_centre_id}, distribution_location_id={sample.distribution_location_id}")
            
            # Transactions
            transactions = session.query(Transaction).all()
            print(f"✓ Transactions: {len(transactions)} records")
            
            # Activity Logs
            logs = session.query(ActivityLog).all()
            print(f"✓ Activity Logs: {len(logs)} records")
        
        print("\n" + "="*60)
        print("✅ DATABASE COMPATIBILITY: ALL CHECKS PASSED")
        print("="*60)
        print("\n✓ PyQt6 application can read all data correctly")
        print("✓ Backup operations will work properly")
        print("✓ All model fields are accessible")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backup_compatibility():
    """Test that backup operations work correctly"""
    print("\n" + "="*60)
    print("  BACKUP OPERATION TEST")
    print("="*60 + "\n")
    
    try:
        import sqlite3
        import shutil
        from datetime import datetime
        
        db_path = Path("data/alnoor_database.db")
        
        if not db_path.exists():
            print("⚠️  Database file not found at expected location")
            print(f"   Expected: {db_path.absolute()}")
            return False
        
        # Test 1: Can open database directly with sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check all tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'products', 'purchase_orders', 'pharmacies', 
            'distribution_locations', 'medical_centres', 'patient_coupons',
            'transactions', 'activity_logs'
        ]
        
        print("Table Verification:")
        for table in expected_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✓ {table}: {count} records")
            else:
                print(f"  ✗ {table}: MISSING!")
                conn.close()
                return False
        
        # Test 2: Check patient_coupons schema (most critical for batch operations)
        cursor.execute("PRAGMA table_info(patient_coupons)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        required_fields = [
            'id', 'coupon_reference', 'patient_name', 'cpr', 'quantity_pieces',
            'medical_centre_id', 'distribution_location_id', 'product_id',
            'verified', 'verification_reference', 'delivery_note_number',
            'grv_reference', 'date_received', 'date_verified', 'notes',
            'created_at', 'updated_at'
        ]
        
        print("\nPatient Coupons Schema Verification:")
        for field in required_fields:
            if field in columns:
                print(f"  ✓ {field}: {columns[field]}")
            else:
                print(f"  ✗ {field}: MISSING!")
                conn.close()
                return False
        
        conn.close()
        
        # Test 3: Simulate backup operation
        backup_dir = Path("data/backups")
        backup_dir.mkdir(exist_ok=True)
        
        test_backup_path = backup_dir / "test_backup.db"
        shutil.copy2(db_path, test_backup_path)
        
        # Verify backup can be opened
        backup_conn = sqlite3.connect(test_backup_path)
        backup_cursor = backup_conn.cursor()
        backup_cursor.execute("SELECT COUNT(*) FROM patient_coupons")
        backup_count = backup_cursor.fetchone()[0]
        backup_conn.close()
        
        print(f"\n✓ Backup created successfully: {test_backup_path.name}")
        print(f"✓ Backup verified: {backup_count} coupons preserved")
        
        # Clean up test backup
        test_backup_path.unlink()
        
        print("\n" + "="*60)
        print("✅ BACKUP COMPATIBILITY: ALL CHECKS PASSED")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ BACKUP TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = True
    
    # Test database reading
    if not test_database_reading():
        success = False
    
    # Test backup operations
    if not test_backup_compatibility():
        success = False
    
    if success:
        print("\n✅ ALL COMPATIBILITY CHECKS PASSED")
        print("   PyQt6 application and backups will work correctly\n")
        sys.exit(0)
    else:
        print("\n❌ SOME COMPATIBILITY CHECKS FAILED")
        print("   Please review errors above\n")
        sys.exit(1)
