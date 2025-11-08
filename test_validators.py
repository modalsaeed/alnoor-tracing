"""
Quick test script to verify validators work correctly.
Run this to test the validators module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils import (
    validate_cpr,
    validate_reference,
    validate_po_reference,
    validate_quantity,
    validate_name,
    validate_phone,
    validate_email,
    sanitize_input,
    normalize_reference,
)


def test_validate_cpr():
    """Test CPR validation."""
    print("Testing CPR validation...")
    
    # Valid CPRs
    assert validate_cpr("123456789")[0] == True, "Valid CPR should pass"
    assert validate_cpr("12345")[0] == True, "5-digit CPR should pass"
    
    # Invalid CPRs
    assert validate_cpr("1234")[0] == False, "Too short CPR should fail"
    assert validate_cpr("")[0] == False, "Empty CPR should fail"
    assert validate_cpr("ABC123")[0] == False, "Non-numeric CPR should fail"
    
    print("✅ CPR validation tests passed!")


def test_validate_reference():
    """Test reference validation."""
    print("\nTesting reference validation...")
    
    # Valid references
    assert validate_reference("PROD-001")[0] == True, "Valid reference should pass"
    assert validate_reference("AB")[0] == True, "2-char reference should pass"
    assert validate_reference("Item_123")[0] == True, "Underscore should be allowed"
    
    # Invalid references
    assert validate_reference("A")[0] == False, "Too short reference should fail"
    assert validate_reference("")[0] == False, "Empty reference should fail"
    assert validate_reference("REF@123")[0] == False, "Special chars should fail"
    
    print("✅ Reference validation tests passed!")


def test_validate_quantity():
    """Test quantity validation."""
    print("\nTesting quantity validation...")
    
    # Valid quantities
    assert validate_quantity(1)[0] == True, "Quantity 1 should pass"
    assert validate_quantity(100)[0] == True, "Quantity 100 should pass"
    assert validate_quantity(1000000)[0] == True, "Max quantity should pass"
    
    # Invalid quantities
    assert validate_quantity(0)[0] == False, "Zero quantity should fail"
    assert validate_quantity(-1)[0] == False, "Negative quantity should fail"
    assert validate_quantity(1000001)[0] == False, "Quantity > 1M should fail"
    
    print("✅ Quantity validation tests passed!")


def test_validate_name():
    """Test name validation."""
    print("\nTesting name validation...")
    
    # Valid names
    assert validate_name("John Doe")[0] == True, "Valid name should pass"
    assert validate_name("Mohammed Al-Khalifa")[0] == True, "Name with hyphen should pass"
    assert validate_name("O'Brien")[0] == True, "Name with apostrophe should pass"
    
    # Invalid names
    assert validate_name("AB")[0] == False, "Too short name should fail"
    assert validate_name("")[0] == False, "Empty name should fail"
    assert validate_name("Name@123")[0] == False, "Name with @ should fail"
    
    print("✅ Name validation tests passed!")


def test_validate_phone():
    """Test phone validation."""
    print("\nTesting phone validation...")
    
    # Valid phones
    assert validate_phone("+973 1234 5678")[0] == True, "Valid phone should pass"
    assert validate_phone("12345")[0] == True, "5-digit phone should pass"
    assert validate_phone("", required=False)[0] == True, "Empty optional phone should pass"
    
    # Invalid phones
    assert validate_phone("1234")[0] == False, "Too short phone should fail"
    assert validate_phone("", required=True)[0] == False, "Empty required phone should fail"
    assert validate_phone("ABC123")[0] == False, "Non-numeric phone should fail"
    
    print("✅ Phone validation tests passed!")


def test_validate_email():
    """Test email validation."""
    print("\nTesting email validation...")
    
    # Valid emails
    assert validate_email("user@example.com")[0] == True, "Valid email should pass"
    assert validate_email("test.user@sub.domain.com")[0] == True, "Complex email should pass"
    
    # Invalid emails
    assert validate_email("notanemail")[0] == False, "No @ should fail"
    assert validate_email("@example.com")[0] == False, "Missing local part should fail"
    assert validate_email("user@")[0] == False, "Missing domain should fail"
    
    print("✅ Email validation tests passed!")


def test_sanitize_input():
    """Test input sanitization."""
    print("\nTesting input sanitization...")
    
    # Test sanitization
    assert sanitize_input("  Hello  ") == "Hello", "Should trim whitespace"
    assert sanitize_input("Hello\x00World") == "HelloWorld", "Should remove null bytes"
    assert sanitize_input("Test\nLine") == "Test\nLine", "Should keep newlines"
    assert sanitize_input("Test\tTab") == "Test\tTab", "Should keep tabs"
    
    print("✅ Input sanitization tests passed!")


def test_normalize_reference():
    """Test reference normalization."""
    print("\nTesting reference normalization...")
    
    # Test normalization
    assert normalize_reference("prod-001") == "PROD-001", "Should convert to uppercase"
    assert normalize_reference("  REF-123  ") == "REF-123", "Should trim and uppercase"
    assert normalize_reference("Item_abc") == "ITEM_ABC", "Should uppercase underscores"
    
    print("✅ Reference normalization tests passed!")


def run_all_tests():
    """Run all validation tests."""
    print("=" * 60)
    print("Running Validator Tests")
    print("=" * 60)
    
    try:
        test_validate_cpr()
        test_validate_reference()
        test_validate_quantity()
        test_validate_name()
        test_validate_phone()
        test_validate_email()
        test_sanitize_input()
        test_normalize_reference()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 60)
        print("\nValidators are working correctly!")
        print("You can now use them confidently in your dialogs.")
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED!")
        print("=" * 60)
        print(f"\nError: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
