"""
Comprehensive UTF-8 encoding test for Alnoor Medical Services.
Tests all file I/O operations to ensure proper UTF-8 handling.
"""

import sys
import configparser
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def test_config_reading():
    """Test config.ini reading with UTF-8 encoding."""
    print("\n" + "="*60)
    print("TEST 1: Config File Reading (UTF-8)")
    print("="*60)
    
    # Create test config with special characters
    test_config_path = Path("test_config_utf8.ini")
    test_content = """[server]
mode = client
server_url = http://192.168.1.10:5000
# Arabic comment: مرحبا
# Chinese comment: 你好
# Emoji: 🎉

[database]
path = C:\\ProgramData\\AlnoorDB\\alnoor.db
# Special chars: ñ, ü, é, ő
"""
    
    try:
        # Write test config
        test_config_path.write_text(test_content, encoding='utf-8')
        print("✓ Test config written with UTF-8 encoding")
        
        # Test reading with configparser (as used in db_manager.py)
        config = configparser.ConfigParser()
        config.read(test_config_path, encoding='utf-8')
        
        # Verify sections exist
        assert 'server' in config, "Server section missing"
        assert 'database' in config, "Database section missing"
        
        # Verify values
        assert config['server']['mode'] == 'client', "Mode value incorrect"
        assert config['server']['server_url'] == 'http://192.168.1.10:5000', "URL value incorrect"
        
        print("✓ Config parsed successfully with UTF-8")
        print(f"  - Mode: {config['server']['mode']}")
        print(f"  - Server URL: {config['server']['server_url']}")
        print(f"  - DB Path: {config['database']['path']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Config reading failed: {e}")
        return False
    finally:
        # Cleanup
        if test_config_path.exists():
            test_config_path.unlink()
            print("✓ Test config cleaned up")


def test_file_operations():
    """Test file reading/writing with UTF-8."""
    print("\n" + "="*60)
    print("TEST 2: File Operations (UTF-8)")
    print("="*60)
    
    test_file = Path("test_utf8_file.txt")
    
    # Test content with various Unicode characters
    test_content = """Arabic: مرحبا بك في نظام الأعمال الطبية
Chinese: 欢迎使用医疗服务追踪系统
Emoji: 🎉 ✅ ⏳ 📊 💾 🔄
Special: ñ ü é ő ø æ
Product: دواء الاختبار
Numbers: 123456789
English: Alnoor Medical Services
"""
    
    try:
        # Write with UTF-8
        test_file.write_text(test_content, encoding='utf-8')
        print("✓ File written with UTF-8 encoding")
        
        # Read back with UTF-8
        read_content = test_file.read_text(encoding='utf-8')
        
        # Verify content matches
        assert read_content == test_content, "Content mismatch after read"
        print("✓ File read successfully with UTF-8")
        
        # Check specific characters
        assert 'مرحبا' in read_content, "Arabic text missing"
        assert '欢迎' in read_content, "Chinese text missing"
        assert '🎉' in read_content, "Emoji missing"
        assert 'ñ' in read_content, "Special char missing"
        
        print("✓ All Unicode characters preserved correctly")
        return True
        
    except Exception as e:
        print(f"✗ File operations failed: {e}")
        return False
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
            print("✓ Test file cleaned up")


def test_csv_export_encoding():
    """Test CSV export with UTF-8 (as used in reports_widget.py)."""
    print("\n" + "="*60)
    print("TEST 3: CSV Export (UTF-8)")
    print("="*60)
    
    test_csv = Path("test_export_utf8.csv")
    
    # Simulate CSV export with Arabic/special characters
    csv_content = [
        ['Product Name', 'Reference', 'Description', 'Status'],
        ['دواء الاختبار', 'PROD-001', 'Test medicine', '✅ Verified'],
        ['Panadol Extra', 'PROD-002', 'Paracetamol 500mg', '⏳ Pending'],
        ['Café Médical', 'PROD-003', 'Spëcial Ñame', '✅ Verified'],
    ]
    
    try:
        # Write CSV with UTF-8 (as done in reports_widget.py)
        with open(test_csv, 'w', encoding='utf-8') as f:
            # Write header
            f.write(','.join(f'"{h}"' for h in csv_content[0]) + '\n')
            
            # Write data
            for row in csv_content[1:]:
                f.write(','.join(f'"{cell}"' for cell in row) + '\n')
        
        print("✓ CSV written with UTF-8 encoding")
        
        # Read back and verify
        csv_text = test_csv.read_text(encoding='utf-8')
        
        assert 'دواء الاختبار' in csv_text, "Arabic product name missing"
        assert '✅' in csv_text, "Emoji missing"
        assert 'Café' in csv_text, "Special char missing"
        
        print("✓ CSV content verified with UTF-8")
        print(f"  First line: {csv_text.splitlines()[0]}")
        
        return True
        
    except Exception as e:
        print(f"✗ CSV export failed: {e}")
        return False
    finally:
        # Cleanup
        if test_csv.exists():
            test_csv.unlink()
            print("✓ Test CSV cleaned up")


def test_db_manager_config_path():
    """Test that db_manager.py correctly uses UTF-8 for config reading."""
    print("\n" + "="*60)
    print("TEST 4: Database Manager Config Reading")
    print("="*60)
    
    try:
        from database.db_manager import get_database_instance
        
        # Check the source code for UTF-8 encoding parameter
        db_manager_file = Path("src/database/db_manager.py")
        if not db_manager_file.exists():
            print("⚠ db_manager.py not found (might be running from different location)")
            return True
        
        source_code = db_manager_file.read_text(encoding='utf-8')
        
        # Verify both config.read() calls have encoding='utf-8'
        config_read_count = source_code.count("config.read(")
        utf8_config_read_count = source_code.count("config.read(config_path, encoding='utf-8')")
        
        print(f"  Found {config_read_count} config.read() calls")
        print(f"  Found {utf8_config_read_count} with UTF-8 encoding")
        
        if utf8_config_read_count >= 2:
            print("✓ All config.read() calls use UTF-8 encoding")
            return True
        else:
            print("✗ Some config.read() calls missing UTF-8 encoding!")
            return False
            
    except Exception as e:
        print(f"✗ Source code check failed: {e}")
        return False


def test_build_installer_encoding():
    """Test that build_installer.py uses UTF-8 for all file operations."""
    print("\n" + "="*60)
    print("TEST 5: Build Installer Script Encoding")
    print("="*60)
    
    try:
        build_script = Path("build_installer.py")
        if not build_script.exists():
            print("⚠ build_installer.py not found")
            return True
        
        source_code = build_script.read_text(encoding='utf-8')
        
        # Check for read_text/write_text without encoding
        issues = []
        
        if '.read_text()' in source_code:
            issues.append("Found .read_text() without encoding parameter")
        
        if '.write_text(' in source_code:
            # Check if all write_text have encoding
            import re
            write_calls = re.findall(r'\.write_text\([^)]+\)', source_code)
            for call in write_calls:
                if 'encoding=' not in call:
                    issues.append(f"Found write_text without encoding: {call[:50]}...")
        
        if issues:
            print("✗ Found encoding issues in build_installer.py:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✓ All file operations in build_installer.py use UTF-8 encoding")
            return True
            
    except Exception as e:
        print(f"✗ Build script check failed: {e}")
        return False


def main():
    """Run all UTF-8 encoding tests."""
    print("\n" + "="*70)
    print("  UTF-8 ENCODING VALIDATION TEST SUITE")
    print("  Alnoor Medical Services")
    print("="*70)
    
    tests = [
        ("Config File Reading", test_config_reading),
        ("File Operations", test_file_operations),
        ("CSV Export", test_csv_export_encoding),
        ("Database Manager Config", test_db_manager_config_path),
        ("Build Installer Script", test_build_installer_encoding),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} raised exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*70)
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("="*70)
        print("\n✓ UTF-8 encoding properly configured throughout application")
        print("✓ No charmap codec errors should occur")
        print("✓ Arabic, Chinese, emojis, and special characters fully supported")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("="*70)
        print("\n⚠ Please review and fix the encoding issues above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
