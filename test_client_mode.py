"""
Test script to verify API client mode connection in dev environment.

Usage:
    1. Make sure server is running on the target PC
    2. Create config.ini with:
       [server]
       mode = client
       server_url = http://192.168.100.155:5000
    3. Run: python test_client_mode.py

This will test the connection without launching the full app.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import get_database_instance, get_connection_debug_info


def main():
    print("="*70)
    print("TESTING API CLIENT MODE CONNECTION")
    print("="*70)
    print()
    
    try:
        # Get database instance (will check config and return client or local)
        db = get_database_instance()
        
        # Show debug info
        debug_info = get_connection_debug_info()
        if debug_info:
            print("\n📋 Connection Debug Info:")
            print("-" * 70)
            for line in debug_info:
                print(f"  {line}")
            print("-" * 70)
        
        # Check what type of connection we got
        from src.database.db_client import DatabaseClient
        from src.database.db_manager import DatabaseManager
        
        if isinstance(db, DatabaseClient):
            print("\n✅ SUCCESS: Connected in API CLIENT mode")
            print(f"   Server URL: {db.server_url}")
            
            # Test a simple API call
            print("\n🔄 Testing API connection...")
            try:
                # Try to get products (will fail if server is down)
                from src.database.models import Product
                products = db.get_all(Product)
                print(f"   ✅ API is responding!")
                print(f"   📦 Found {len(products)} products in database")
            except Exception as e:
                print(f"   ⚠️  API connection failed: {e}")
                
        elif isinstance(db, DatabaseManager):
            print("\n💾 INFO: Running in LOCAL DATABASE mode")
            print(f"   Database: {db.db_path}")
            print("\n   To test client mode:")
            print("   1. Create config.ini in project root with:")
            print("      [server]")
            print("      mode = client")
            print("      server_url = http://YOUR-SERVER-IP:5000")
            print("   2. Run this script again")
        
        print("\n" + "="*70)
        print("✅ Connection test completed!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
