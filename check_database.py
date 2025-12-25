"""
Quick database checker for API server.
Shows database location, size, and record counts.
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def check_database():
    """Check database status and show statistics"""
    
    # Database path (same as API server uses in development)
    db_path = Path("data/alnoor.db")
    
    print("\n" + "="*60)
    print("📊 DATABASE STATUS CHECK")
    print("="*60)
    
    # Check if database exists
    if not db_path.exists():
        print("\n❌ Database file NOT FOUND!")
        print(f"   Expected location: {db_path.absolute()}")
        print("\n💡 This is normal if:")
        print("   - Server hasn't been started yet")
        print("   - Database in different location (check server output)")
        return False
    
    print(f"\n✅ Database file found")
    print(f"📁 Location: {db_path.absolute()}")
    
    # Get file size
    file_size = db_path.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"💾 Size: {size_mb:.2f} MB ({file_size:,} bytes)")
    
    # Get modification time
    mod_time = datetime.fromtimestamp(db_path.stat().st_mtime)
    print(f"📅 Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect and get table statistics
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("📋 TABLE STATISTICS")
        print("="*60)
        
        # Define tables to check
        tables = [
            ('products', 'Products'),
            ('purchase_orders', 'Purchase Orders'),
            ('pharmacies', 'Pharmacies'),
            ('distribution_locations', 'Distribution Locations'),
            ('medical_centres', 'Medical Centres'),
            ('patient_coupons', 'Patient Coupons'),
            ('transactions', 'Transactions'),
            ('activity_logs', 'Activity Logs'),
        ]
        
        total_records = 0
        for table_name, display_name in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_records += count
                
                # Add emoji indicators
                if count > 0:
                    if count > 100:
                        indicator = "🟢"  # Many records
                    elif count > 10:
                        indicator = "🟡"  # Some records
                    else:
                        indicator = "🟠"  # Few records
                else:
                    indicator = "⚪"  # No records
                
                print(f"  {indicator} {display_name:25} {count:>6,} records")
            except sqlite3.Error as e:
                print(f"  ❌ {display_name:25} Error: {e}")
        
        print("  " + "-"*56)
        print(f"  📊 Total Records: {total_records:,}")
        
        # Check recent activity
        print("\n" + "="*60)
        print("🕐 RECENT ACTIVITY")
        print("="*60)
        
        try:
            cursor.execute("""
                SELECT action_type, table_name, COUNT(*) as count
                FROM activity_logs
                WHERE timestamp > datetime('now', '-1 day')
                GROUP BY action_type, table_name
                ORDER BY count DESC
                LIMIT 5
            """)
            
            recent = cursor.fetchall()
            if recent:
                print("\n  Last 24 hours:")
                for action, table, count in recent:
                    print(f"    • {action} on {table}: {count} times")
            else:
                print("\n  ℹ️  No activity in last 24 hours")
        except sqlite3.Error:
            print("\n  ℹ️  Activity log not available")
        
        # Check verified coupons
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) as verified,
                    SUM(CASE WHEN verified = 0 THEN 1 ELSE 0 END) as pending
                FROM patient_coupons
            """)
            
            total, verified, pending = cursor.fetchone()
            if total > 0:
                print("\n" + "="*60)
                print("📦 COUPON STATUS")
                print("="*60)
                print(f"  Total:     {total:,}")
                print(f"  ✅ Verified: {verified:,} ({verified/total*100:.1f}%)")
                print(f"  ⏳ Pending:  {pending:,} ({pending/total*100:.1f}%)")
        except sqlite3.Error:
            pass
        
        conn.close()
        
        print("\n" + "="*60)
        if total_records > 0:
            print("✅ DATABASE IS ACTIVE AND CONTAINS DATA")
        else:
            print("⚠️  DATABASE IS EMPTY")
            print("   This is normal for a new installation")
        print("="*60)
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Error reading database: {e}")
        return False


def main():
    """Main function"""
    success = check_database()
    
    print("\n" + "="*60)
    print("💡 TIPS")
    print("="*60)
    
    if success:
        print("\n✅ To view/edit database:")
        print("   1. Download DB Browser: https://sqlitebrowser.org/")
        print("   2. Open: data/alnoor.db")
        print("   3. Browse Data tab to see records")
        
        print("\n📊 To monitor server:")
        print("   1. Check logs: logs/api_server_YYYYMMDD.log")
        print("   2. Watch in real-time:")
        print("      Get-Content logs\\api_server_*.log -Wait")
    else:
        print("\n💡 To create database:")
        print("   1. Start the API server:")
        print("      .venv\\Scripts\\python.exe src\\api_server.py")
        print("   2. Database will be created automatically")
    
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()
