"""
Unit Tests for Validators Module

Tests all validation functions in src/utils/validators.py
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.validators import (
    ValidationError,
    validate_cpr,
    validate_reference,
    validate_po_reference,
    validate_quantity,
    validate_name,
    validate_phone,
    validate_email,
    validate_date_range,
    validate_required_field,
    sanitize_input,
    normalize_reference
)


class TestValidateCPR(unittest.TestCase):
    """Test CPR validation."""
    
    def test_valid_cpr(self):
        """Test valid CPR numbers."""
        valid, msg = validate_cpr("123456789")
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = validate_cpr("12345")
        self.assertTrue(valid)
        
    def test_valid_cpr_with_formatting(self):
        """Test CPR with spaces and dashes."""
        valid, msg = validate_cpr("123-456-789")
        self.assertTrue(valid)
        
        valid, msg = validate_cpr("123 456 789")
        self.assertTrue(valid)
        
    def test_empty_cpr(self):
        """Test empty CPR."""
        valid, msg = validate_cpr("")
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())
        
    def test_non_numeric_cpr(self):
        """Test CPR with non-numeric characters."""
        valid, msg = validate_cpr("ABC123456")
        self.assertFalse(valid)
        self.assertIn("numbers", msg.lower())
        
    def test_too_short_cpr(self):
        """Test CPR that's too short."""
        valid, msg = validate_cpr("1234")
        self.assertFalse(valid)
        self.assertIn("at least 5", msg.lower())
        
    def test_too_long_cpr(self):
        """Test CPR that's too long."""
        valid, msg = validate_cpr("1234567890123456")  # 16 digits
        self.assertFalse(valid)
        self.assertIn("exceed 15", msg.lower())


class TestValidateReference(unittest.TestCase):
    """Test reference validation."""
    
    def test_valid_reference(self):
        """Test valid references."""
        valid, msg = validate_reference("REF123")
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = validate_reference("REF-123_ABC")
        self.assertTrue(valid)
        
    def test_empty_reference(self):
        """Test empty reference."""
        valid, msg = validate_reference("")
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())
        
    def test_reference_with_whitespace(self):
        """Test reference with leading/trailing whitespace."""
        valid, msg = validate_reference("  REF123  ")
        self.assertTrue(valid)  # Should strip whitespace
        
    def test_too_short_reference(self):
        """Test reference that's too short."""
        valid, msg = validate_reference("R", min_length=2)
        self.assertFalse(valid)
        self.assertIn("at least 2", msg.lower())
        
    def test_too_long_reference(self):
        """Test reference that's too long."""
        valid, msg = validate_reference("R" * 51, max_length=50)
        self.assertFalse(valid)
        self.assertIn("exceed 50", msg.lower())
        
    def test_invalid_characters(self):
        """Test reference with invalid characters."""
        valid, msg = validate_reference("REF@123")
        self.assertFalse(valid)
        self.assertIn("letters, numbers, dashes", msg.lower())
        
        valid, msg = validate_reference("REF 123")  # Space not allowed
        self.assertFalse(valid)


class TestValidatePOReference(unittest.TestCase):
    """Test Purchase Order reference validation."""
    
    def test_valid_po_reference(self):
        """Test valid PO references."""
        valid, msg = validate_po_reference("PO-2024-001")
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = validate_po_reference("PO123")
        self.assertTrue(valid)
        
        valid, msg = validate_po_reference("PO/2024/001")
        self.assertTrue(valid)
        
    def test_empty_po_reference(self):
        """Test empty PO reference."""
        valid, msg = validate_po_reference("")
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())
        
    def test_too_short_po_reference(self):
        """Test PO reference that's too short."""
        valid, msg = validate_po_reference("P")
        self.assertFalse(valid)
        self.assertIn("at least 2", msg.lower())
        
    def test_invalid_po_characters(self):
        """Test PO reference with invalid characters."""
        valid, msg = validate_po_reference("PO@2024")
        self.assertFalse(valid)
        self.assertIn("letters, numbers", msg.lower())


class TestValidateQuantity(unittest.TestCase):
    """Test quantity validation."""
    
    def test_valid_quantity(self):
        """Test valid quantities."""
        valid, msg = validate_quantity(1)
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = validate_quantity(100)
        self.assertTrue(valid)
        
        valid, msg = validate_quantity(999999)
        self.assertTrue(valid)
        
    def test_minimum_quantity(self):
        """Test minimum quantity validation."""
        valid, msg = validate_quantity(0, min_qty=1)
        self.assertFalse(valid)
        self.assertIn("at least 1", msg.lower())
        
        valid, msg = validate_quantity(5, min_qty=10)
        self.assertFalse(valid)
        self.assertIn("at least 10", msg.lower())
        
    def test_maximum_quantity(self):
        """Test maximum quantity validation."""
        valid, msg = validate_quantity(1000001, max_qty=1000000)
        self.assertFalse(valid)
        self.assertIn("exceed", msg.lower())
        
    def test_negative_quantity(self):
        """Test negative quantity."""
        valid, msg = validate_quantity(-5)
        self.assertFalse(valid)
        self.assertIn("at least", msg.lower())


class TestValidateName(unittest.TestCase):
    """Test name validation."""
    
    def test_valid_name(self):
        """Test valid names."""
        valid, msg = validate_name("John Doe")
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = validate_name("Product-123")
        self.assertTrue(valid)
        
    def test_empty_name(self):
        """Test empty name."""
        valid, msg = validate_name("")
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())
        
    def test_name_with_whitespace(self):
        """Test name with leading/trailing whitespace."""
        valid, msg = validate_name("  John Doe  ")
        self.assertTrue(valid)  # Should strip whitespace
        
    def test_too_short_name(self):
        """Test name that's too short."""
        valid, msg = validate_name("Jo", min_length=3)
        self.assertFalse(valid)
        self.assertIn("at least 3", msg.lower())
        
    def test_too_long_name(self):
        """Test name that's too long."""
        valid, msg = validate_name("A" * 101, max_length=100)
        self.assertFalse(valid)
        self.assertIn("exceed 100", msg.lower())
        
    def test_custom_field_name(self):
        """Test custom field name in error message."""
        valid, msg = validate_name("Jo", min_length=3, field_name="Product Name")
        self.assertFalse(valid)
        self.assertIn("Product Name", msg)


class TestValidatePhone(unittest.TestCase):
    """Test phone validation."""
    
    def test_valid_phone(self):
        """Test valid phone numbers."""
        valid, msg = validate_phone("12345678")
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = validate_phone("+973-12345678")
        self.assertTrue(valid)
        
        valid, msg = validate_phone("(123) 456-7890")
        self.assertTrue(valid)
        
    def test_empty_phone_optional(self):
        """Test empty phone when optional."""
        valid, msg = validate_phone("", required=False)
        self.assertTrue(valid)  # Optional, so empty is OK
        
    def test_empty_phone_required(self):
        """Test empty phone when required."""
        valid, msg = validate_phone("", required=True)
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())
        
    def test_invalid_phone_characters(self):
        """Test phone with invalid characters."""
        valid, msg = validate_phone("123ABC456")
        self.assertFalse(valid)
        self.assertIn("digits", msg.lower())
        
    def test_phone_too_short(self):
        """Test phone that's too short."""
        valid, msg = validate_phone("1234")
        self.assertFalse(valid)
        self.assertIn("at least 5", msg.lower())
        
    def test_phone_too_long(self):
        """Test phone that's too long."""
        valid, msg = validate_phone("1234567890123456")  # 16 digits
        self.assertFalse(valid)
        self.assertIn("exceed 15", msg.lower())


class TestValidateEmail(unittest.TestCase):
    """Test email validation."""
    
    def test_valid_email(self):
        """Test valid emails."""
        valid, msg = validate_email("user@example.com")
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = validate_email("user.name+tag@example.co.uk")
        self.assertTrue(valid)
        
    def test_empty_email_optional(self):
        """Test empty email when optional."""
        valid, msg = validate_email("", required=False)
        self.assertTrue(valid)  # Optional, so empty is OK
        
    def test_empty_email_required(self):
        """Test empty email when required."""
        valid, msg = validate_email("", required=True)
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())
        
    def test_invalid_email_format(self):
        """Test invalid email formats."""
        valid, msg = validate_email("notanemail")
        self.assertFalse(valid)
        self.assertIn("invalid", msg.lower())
        
        valid, msg = validate_email("missing@domain")
        self.assertFalse(valid)
        
        valid, msg = validate_email("@nodomain.com")
        self.assertFalse(valid)
        
    def test_email_too_long(self):
        """Test email that's too long."""
        long_email = "a" * 250 + "@test.com"
        valid, msg = validate_email(long_email)
        self.assertFalse(valid)
        self.assertIn("too long", msg.lower())


class TestValidateDateRange(unittest.TestCase):
    """Test date range validation."""
    
    def test_valid_date_range(self):
        """Test valid date ranges."""
        date_from = datetime.now()
        date_to = datetime.now() + timedelta(days=30)
        valid, msg = validate_date_range(date_from, date_to)
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
    def test_same_date(self):
        """Test same start and end date."""
        date = datetime.now()
        valid, msg = validate_date_range(date, date)
        self.assertTrue(valid)  # Same date should be valid
        
    def test_invalid_date_order(self):
        """Test invalid date order (start after end)."""
        date_from = datetime.now() + timedelta(days=30)
        date_to = datetime.now()
        valid, msg = validate_date_range(date_from, date_to)
        self.assertFalse(valid)
        self.assertIn("before", msg.lower())
        
    def test_date_range_too_large(self):
        """Test date range that's too large."""
        date_from = datetime.now()
        date_to = datetime.now() + timedelta(days=3651)  # >10 years
        valid, msg = validate_date_range(date_from, date_to)
        self.assertFalse(valid)
        self.assertIn("exceed", msg.lower())


class TestValidateRequiredField(unittest.TestCase):
    """Test required field validation."""
    
    def test_valid_required_field(self):
        """Test valid required fields."""
        valid, msg = validate_required_field("some value", "Field")
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = validate_required_field(123, "Number")
        self.assertTrue(valid)
        
    def test_none_value(self):
        """Test None value."""
        valid, msg = validate_required_field(None, "Field")
        self.assertFalse(valid)
        self.assertIn("Field", msg)
        self.assertIn("required", msg.lower())
        
    def test_empty_string(self):
        """Test empty string."""
        valid, msg = validate_required_field("", "Field")
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())
        
    def test_whitespace_only(self):
        """Test whitespace-only string."""
        valid, msg = validate_required_field("   ", "Field")
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())


class TestSanitizeInput(unittest.TestCase):
    """Test input sanitization."""
    
    def test_clean_text(self):
        """Test clean text passes through."""
        text = "Hello World"
        sanitized = sanitize_input(text)
        self.assertEqual(sanitized, text)
        
    def test_whitespace_trimming(self):
        """Test leading/trailing whitespace is removed."""
        text = "  Hello World  "
        sanitized = sanitize_input(text)
        self.assertEqual(sanitized, "Hello World")
        
    def test_null_byte_removal(self):
        """Test null bytes are removed."""
        text = "Hello\x00World"
        sanitized = sanitize_input(text)
        self.assertNotIn("\x00", sanitized)
        
    def test_control_character_removal(self):
        """Test control characters are removed."""
        text = "Hello\x01\x02World"
        sanitized = sanitize_input(text)
        self.assertEqual(sanitized, "HelloWorld")
        
    def test_newline_preserved(self):
        """Test newlines are preserved."""
        text = "Hello\nWorld"
        sanitized = sanitize_input(text)
        self.assertIn("\n", sanitized)
        
    def test_tab_preserved(self):
        """Test tabs are preserved."""
        text = "Hello\tWorld"
        sanitized = sanitize_input(text)
        self.assertIn("\t", sanitized)
        
    def test_empty_text(self):
        """Test empty text."""
        sanitized = sanitize_input("")
        self.assertEqual(sanitized, "")
        
    def test_none_text(self):
        """Test None text."""
        sanitized = sanitize_input(None)
        self.assertEqual(sanitized, "")


class TestNormalizeReference(unittest.TestCase):
    """Test reference normalization."""
    
    def test_uppercase_conversion(self):
        """Test uppercase conversion."""
        ref = "ref-123"
        normalized = normalize_reference(ref)
        self.assertEqual(normalized, "REF-123")
        
    def test_whitespace_removal(self):
        """Test whitespace removal."""
        ref = " REF-123 "
        normalized = normalize_reference(ref)
        self.assertEqual(normalized, "REF-123")
        
    def test_empty_reference(self):
        """Test empty reference."""
        normalized = normalize_reference("")
        self.assertEqual(normalized, "")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
