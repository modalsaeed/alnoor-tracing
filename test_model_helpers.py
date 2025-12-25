"""
Test script to verify all widgets can handle both ORM objects and dictionaries.

This tests the model_helpers functions with various data types.
"""

from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr


def test_with_dict():
    """Test with dictionary data (like from API)"""
    print("Testing with dictionaries...")
    
    product_dict = {'id': 1, 'name': 'Aspirin', 'reference': 'ASP-001'}
    coupon_dict = {
        'id': 100,
        'patient_name': 'John Doe',
        'product': {'id': 1, 'name': 'Aspirin'},
        'medical_centre': {'id': 5, 'name': 'Health Centre A'}
    }
    
    # Test simple attributes
    assert get_id(product_dict) == 1
    assert get_name(product_dict) == 'Aspirin'
    assert get_attr(product_dict, 'reference') == 'ASP-001'
    
    # Test nested attributes
    assert get_nested_attr(coupon_dict, 'product.name') == 'Aspirin'
    assert get_nested_attr(coupon_dict, 'medical_centre.name') == 'Health Centre A'
    assert get_nested_attr(coupon_dict, 'product.id') == 1
    
    # Test with missing attributes
    assert get_attr(product_dict, 'missing', 'default') == 'default'
    assert get_nested_attr(coupon_dict, 'missing.nested', 'N/A') == 'N/A'
    
    print("✅ Dictionary tests passed!")


def test_with_orm_objects():
    """Test with ORM objects (like from local database)"""
    print("Testing with ORM objects...")
    
    # Create mock ORM-like objects
    class Product:
        def __init__(self):
            self.id = 1
            self.name = 'Aspirin'
            self.reference = 'ASP-001'
    
    class MedicalCentre:
        def __init__(self):
            self.id = 5
            self.name = 'Health Centre A'
    
    class Coupon:
        def __init__(self):
            self.id = 100
            self.patient_name = 'John Doe'
            self.product = Product()
            self.medical_centre = MedicalCentre()
    
    product = Product()
    coupon = Coupon()
    
    # Test simple attributes
    assert get_id(product) == 1
    assert get_name(product) == 'Aspirin'
    assert get_attr(product, 'reference') == 'ASP-001'
    
    # Test nested attributes
    assert get_nested_attr(coupon, 'product.name') == 'Aspirin'
    assert get_nested_attr(coupon, 'medical_centre.name') == 'Health Centre A'
    assert get_nested_attr(coupon, 'product.id') == 1
    
    # Test with missing attributes
    assert get_attr(product, 'missing', 'default') == 'default'
    assert get_nested_attr(coupon, 'missing.nested', 'N/A') == 'N/A'
    
    print("✅ ORM object tests passed!")


def test_with_none():
    """Test with None values"""
    print("Testing with None values...")
    
    assert get_id(None, 0) == 0
    assert get_name(None, 'Unknown') == 'Unknown'
    assert get_attr(None, 'anything', 'default') == 'default'
    assert get_nested_attr(None, 'any.path', 'N/A') == 'N/A'
    
    print("✅ None value tests passed!")


def test_mixed_scenarios():
    """Test complex mixed scenarios"""
    print("Testing mixed scenarios...")
    
    # Dictionary with None nested value
    data = {'id': 1, 'product': None}
    assert get_nested_attr(data, 'product.name', 'N/A') == 'N/A'
    
    # Dictionary with partial nesting
    data = {'id': 1, 'product': {'id': 2}}
    assert get_nested_attr(data, 'product.name', 'Unknown') == 'Unknown'
    
    print("✅ Mixed scenario tests passed!")


if __name__ == '__main__':
    test_with_dict()
    test_with_orm_objects()
    test_with_none()
    test_mixed_scenarios()
    print("\n🎉 All tests passed! The model_helpers work correctly!")
