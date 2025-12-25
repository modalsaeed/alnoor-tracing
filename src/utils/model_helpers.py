"""
Helper functions for working with both ORM models and dictionary objects.

This module provides utilities to access attributes safely whether the data
comes from a local SQLAlchemy session (ORM objects) or from the API (dictionaries).
"""

from typing import Any, Optional


def get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """
    Safely get an attribute from either an ORM object or dictionary.
    
    Args:
        obj: The object (ORM model instance or dictionary)
        attr: The attribute name to access
        default: Default value if attribute doesn't exist
        
    Returns:
        The attribute value or default
    """
    if obj is None:
        return default
    
    # Handle dictionaries
    if isinstance(obj, dict):
        return obj.get(attr, default)
    
    # Handle ORM objects
    return getattr(obj, attr, default)


def get_nested_attr(obj: Any, path: str, default: Any = None) -> Any:
    """
    Safely get a nested attribute from either ORM objects or dictionaries.
    
    Args:
        obj: The root object
        path: Dot-separated path (e.g., "product.name")
        default: Default value if path doesn't exist
        
    Returns:
        The nested attribute value or default
        
    Examples:
        get_nested_attr(coupon, "product.name", "Unknown")
        get_nested_attr(purchase, "product.reference", "N/A")
    """
    if obj is None:
        return default
    
    parts = path.split('.')
    current = obj
    
    for part in parts:
        if current is None:
            return default
        
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    
    return current if current is not None else default


def get_id(obj: Any, default: Any = None) -> Any:
    """Get the id from either an ORM object or dictionary."""
    return get_attr(obj, 'id', default)


def get_name(obj: Any, default: str = "Unknown") -> str:
    """Get the name from either an ORM object or dictionary."""
    return get_attr(obj, 'name', default)
