"""
Validators Module - Input validation utilities.

Provides validation functions for various input types used across the application.
"""

import re
from typing import Tuple, Optional
from datetime import datetime


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_cpr(cpr: str) -> Tuple[bool, str]:
    """
    Validate Civil Personal Record (CPR) number.
    
    Args:
        cpr: CPR number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not cpr:
        return False, "CPR is required."
    
    # Remove spaces and dashes
    cleaned_cpr = cpr.replace(" ", "").replace("-", "")
    
    # Check if it's numeric
    if not cleaned_cpr.isdigit():
        return False, "CPR must contain only numbers."
    
    # Check length (typically 9-12 digits depending on country)
    if len(cleaned_cpr) < 5:
        return False, "CPR must be at least 5 digits."
    
    if len(cleaned_cpr) > 15:
        return False, "CPR cannot exceed 15 digits."
    
    return True, ""


def validate_reference(reference: str, min_length: int = 2, max_length: int = 50) -> Tuple[bool, str]:
    """
    Validate reference code format.
    
    Args:
        reference: Reference code to validate
        min_length: Minimum length (default: 2)
        max_length: Maximum length (default: 50)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not reference:
        return False, "Reference is required."
    
    # Remove leading/trailing whitespace
    reference = reference.strip()
    
    if len(reference) < min_length:
        return False, f"Reference must be at least {min_length} characters."
    
    if len(reference) > max_length:
        return False, f"Reference cannot exceed {max_length} characters."
    
    # Check for valid characters (alphanumeric, dash, underscore)
    if not re.match(r'^[A-Za-z0-9\-_]+$', reference):
        return False, "Reference can only contain letters, numbers, dashes, and underscores."
    
    return True, ""


def validate_po_reference(po_ref: str) -> Tuple[bool, str]:
    """
    Validate Purchase Order reference format.
    
    Expected format: Flexible - any characters allowed
    
    Args:
        po_ref: PO reference to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not po_ref:
        return False, "PO reference is required."
    
    po_ref = po_ref.strip()
    
    if len(po_ref) < 2:
        return False, "PO reference must be at least 2 characters."
    
    # Allow any printable characters including spaces
    return True, ""


def validate_quantity(quantity: int, min_qty: int = 1, max_qty: int = 100000000) -> Tuple[bool, str]:
    """
    Validate quantity value.
    
    Args:
        quantity: Quantity to validate
        min_qty: Minimum allowed quantity (default: 1)
        max_qty: Maximum allowed quantity (default: 100,000,000)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if quantity < min_qty:
        return False, f"Quantity must be at least {min_qty}."
    
    if quantity > max_qty:
        return False, f"Quantity cannot exceed {max_qty:,}."
    
    return True, ""


def validate_name(name: str, min_length: int = 3, max_length: int = 100, field_name: str = "Name") -> Tuple[bool, str]:
    """
    Validate name field (patient name, product name, etc.).
    
    Args:
        name: Name to validate
        min_length: Minimum length (default: 3)
        max_length: Maximum length (default: 100)
        field_name: Name of the field for error messages (default: "Name")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, f"{field_name} is required."
    
    name = name.strip()
    
    if len(name) < min_length:
        return False, f"{field_name} must be at least {min_length} characters."
    
    if len(name) > max_length:
        return False, f"{field_name} cannot exceed {max_length} characters."
    
    # Check for valid characters (allow letters, numbers, spaces, common punctuation)
    if not re.match(r'^[A-Za-z0-9\s\-.,\'()&]+$', name):
        return False, f"{field_name} contains invalid characters."
    
    return True, ""


def validate_phone(phone: str, required: bool = False) -> Tuple[bool, str]:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        required: Whether phone is required (default: False)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not phone:
        if required:
            return False, "Phone number is required."
        return True, ""  # Optional field, empty is ok
    
    # Remove common separators
    cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if numeric (with optional + prefix)
    if not re.match(r'^\+?\d+$', cleaned_phone):
        return False, "Phone number can only contain digits, spaces, dashes, and + prefix."
    
    # Check length (5-15 digits is reasonable for international numbers)
    digits_only = re.sub(r'[^\d]', '', cleaned_phone)
    if len(digits_only) < 5:
        return False, "Phone number must contain at least 5 digits."
    
    if len(digits_only) > 15:
        return False, "Phone number cannot exceed 15 digits."
    
    return True, ""


def validate_email(email: str, required: bool = False) -> Tuple[bool, str]:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        required: Whether email is required (default: False)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        if required:
            return False, "Email is required."
        return True, ""  # Optional field, empty is ok
    
    email = email.strip()
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Invalid email format."
    
    if len(email) > 255:
        return False, "Email address is too long."
    
    return True, ""


def validate_date_range(date_from: datetime, date_to: datetime) -> Tuple[bool, str]:
    """
    Validate date range.
    
    Args:
        date_from: Start date
        date_to: End date
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if date_from > date_to:
        return False, "Start date must be before or equal to end date."
    
    # Check if date range is reasonable (not more than 10 years)
    days_diff = (date_to - date_from).days
    if days_diff > 3650:  # 10 years
        return False, "Date range cannot exceed 10 years."
    
    return True, ""


def validate_required_field(value: any, field_name: str) -> Tuple[bool, str]:
    """
    Validate that a required field is not empty.
    
    Args:
        value: Value to check
        field_name: Name of the field for error message
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} is required."
    
    if isinstance(value, str) and not value.strip():
        return False, f"{field_name} is required."
    
    return True, ""


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing potentially harmful characters.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove any null bytes
    text = text.replace('\x00', '')
    
    # Remove any control characters except newline and tab
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text


def normalize_reference(reference: str) -> str:
    """
    Normalize reference code to uppercase and remove extra spaces.
    
    Args:
        reference: Reference to normalize
        
    Returns:
        Normalized reference
    """
    if not reference:
        return ""
    
    return reference.strip().upper()


# Validation constants
class ValidationConstants:
    """Constants for validation rules."""
    
    # Length constraints
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 100
    MIN_REFERENCE_LENGTH = 2
    MAX_REFERENCE_LENGTH = 50
    MIN_CPR_LENGTH = 5
    MAX_CPR_LENGTH = 15
    
    # Quantity constraints
    MIN_QUANTITY = 1
    MAX_QUANTITY = 100000000
    
    # Phone constraints
    MIN_PHONE_DIGITS = 5
    MAX_PHONE_DIGITS = 15
    
    # Email constraints
    MAX_EMAIL_LENGTH = 255
    
    # Date constraints
    MAX_DATE_RANGE_DAYS = 3650  # 10 years
