"""
Run the application with a test database.

This script creates a temporary test database so you can test functionality
without affecting your production data.
"""

import sys
import os
from pathlib import Path
import shutil
from datetime import datetime

# Set environment variable to use test database
test_db_dir = Path("data/test")
test_db_dir.mkdir(parents=True, exist_ok=True)

test_db_path = test_db_dir / "alnoor_test.db"

# Backup existing test database if it exists
if test_db_path.exists():
    backup_name = f"alnoor_test_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = test_db_dir / backup_name
    shutil.copy2(test_db_path, backup_path)
    print(f"✓ Backed up existing test database to: {backup_path}")
    
    # Ask if user wants to delete the old test database
    response = input("\nDelete old test database and start fresh? (y/n): ").strip().lower()
    if response == 'y':
        test_db_path.unlink()
        print("✓ Deleted old test database")
    else:
        print("✓ Using existing test database")

print(f"\n{'='*60}")
print(f"Starting application with TEST database")
print(f"{'='*60}")
print(f"Database location: {test_db_path.absolute()}")
print(f"{'='*60}\n")

# Set the test database path
os.environ['ALNOOR_TEST_DB'] = str(test_db_path.absolute())

# Import and run the main application
from src.main import main

if __name__ == "__main__":
    sys.exit(main())
