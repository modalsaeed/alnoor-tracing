"""
Database Client for Remote API Access

This module provides HTTP client access to the database API server.
When configured in client mode, all database operations are forwarded
to the API server instead of accessing SQLite directly.
"""

import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class DatabaseClient:
    """
    HTTP client for database API operations.
    Mimics DatabaseManager interface for seamless integration.
    """
    
    def __init__(self, server_url: str):
        """
        Initialize database client.
        
        Args:
            server_url: Base URL of the API server (e.g., http://192.168.1.10:5000)
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to API server"""
        try:
            response = self.session.get(f'{self.server_url}/health', timeout=5)
            response.raise_for_status()
            print(f"✅ Connected to API server: {self.server_url}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Cannot connect to API server at {self.server_url}: {e}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to API server"""
        url = f'{self.server_url}{endpoint}'
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")
    
    # ==================== Product Operations ====================
    
    def get_all_products(self) -> List[Dict]:
        """Get all products"""
        response = self._request('GET', '/products')
        return response.json()
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get product by ID"""
        try:
            response = self._request('GET', f'/products/{product_id}')
            return response.json()
        except RuntimeError:
            return None
    
    def create_product(self, name: str, reference: str, unit: str = None, description: str = None) -> Dict:
        """Create new product"""
        data = {
            'name': name,
            'reference': reference,
            'unit': unit,
            'description': description
        }
        response = self._request('POST', '/products', json=data)
        return response.json()
    
    def update_product(self, product_id: int, **kwargs) -> Dict:
        """Update existing product"""
        response = self._request('PUT', f'/products/{product_id}', json=kwargs)
        return response.json()
    
    def delete_product(self, product_id: int) -> bool:
        """Delete product"""
        try:
            self._request('DELETE', f'/products/{product_id}')
            return True
        except RuntimeError:
            return False
    
    # ==================== Purchase Order Operations ====================
    
    def get_all_purchase_orders(self) -> List[Dict]:
        """Get all purchase orders"""
        response = self._request('GET', '/purchase_orders')
        return response.json()
    
    def get_purchase_order(self, order_id: int) -> Optional[Dict]:
        """Get purchase order by ID"""
        try:
            response = self._request('GET', f'/purchase_orders/{order_id}')
            return response.json()
        except RuntimeError:
            return None
    
    def create_purchase_order(self, product_id: int, quantity: float, 
                            purchase_date: str = None, supplier: str = None, 
                            notes: str = None) -> Dict:
        """Create new purchase order"""
        data = {
            'product_id': product_id,
            'quantity': quantity,
            'purchase_date': purchase_date or datetime.now().isoformat(),
            'supplier': supplier,
            'notes': notes
        }
        response = self._request('POST', '/purchase_orders', json=data)
        return response.json()
    
    def update_purchase_order(self, order_id: int, **kwargs) -> Dict:
        """Update existing purchase order"""
        response = self._request('PUT', f'/purchase_orders/{order_id}', json=kwargs)
        return response.json()
    
    def delete_purchase_order(self, order_id: int) -> bool:
        """Delete purchase order"""
        try:
            self._request('DELETE', f'/purchase_orders/{order_id}')
            return True
        except RuntimeError:
            return False
    
    # ==================== Pharmacy Operations ====================
    
    def get_all_pharmacies(self) -> List[Dict]:
        """Get all pharmacies"""
        response = self._request('GET', '/pharmacies')
        return response.json()
    
    def create_pharmacy(self, name: str, location: str = None, contact: str = None) -> Dict:
        """Create new pharmacy"""
        data = {'name': name, 'location': location, 'contact': contact}
        response = self._request('POST', '/pharmacies', json=data)
        return response.json()
    
    def update_pharmacy(self, pharmacy_id: int, **kwargs) -> Dict:
        """Update existing pharmacy"""
        response = self._request('PUT', f'/pharmacies/{pharmacy_id}', json=kwargs)
        return response.json()
    
    def delete_pharmacy(self, pharmacy_id: int) -> bool:
        """Delete pharmacy"""
        try:
            self._request('DELETE', f'/pharmacies/{pharmacy_id}')
            return True
        except RuntimeError:
            return False
    
    # ==================== Transaction Operations ====================
    
    def get_all_transactions(self, product_id: int = None, 
                           start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get all transactions with optional filtering"""
        params = {}
        if product_id:
            params['product_id'] = product_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        response = self._request('GET', '/transactions', params=params)
        return response.json()
    
    def create_transaction(self, product_id: int, quantity: float, 
                          transaction_type: str, transaction_date: str = None,
                          pharmacy_id: int = None, distribution_location_id: int = None,
                          medical_centre_id: int = None, notes: str = None) -> Dict:
        """Create new transaction"""
        data = {
            'product_id': product_id,
            'quantity': quantity,
            'transaction_type': transaction_type,
            'transaction_date': transaction_date or datetime.now().isoformat(),
            'pharmacy_id': pharmacy_id,
            'distribution_location_id': distribution_location_id,
            'medical_centre_id': medical_centre_id,
            'notes': notes
        }
        response = self._request('POST', '/transactions', json=data)
        return response.json()
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete transaction"""
        try:
            self._request('DELETE', f'/transactions/{transaction_id}')
            return True
        except RuntimeError:
            return False
    
    # ==================== Distribution Location Operations ====================
    
    def get_all_distribution_locations(self) -> List[Dict]:
        """Get all distribution locations"""
        response = self._request('GET', '/distribution_locations')
        return response.json()
    
    def create_distribution_location(self, name: str, address: str = None, contact: str = None) -> Dict:
        """Create new distribution location"""
        data = {'name': name, 'address': address, 'contact': contact}
        response = self._request('POST', '/distribution_locations', json=data)
        return response.json()
    
    # ==================== Medical Centre Operations ====================
    
    def get_all_medical_centres(self) -> List[Dict]:
        """Get all medical centres"""
        response = self._request('GET', '/medical_centres')
        return response.json()
    
    def create_medical_centre(self, name: str, location: str = None, contact: str = None) -> Dict:
        """Create new medical centre"""
        data = {'name': name, 'location': location, 'contact': contact}
        response = self._request('POST', '/medical_centres', json=data)
        return response.json()
    
    # ==================== Patient Coupon Operations ====================
    
    def get_all_patient_coupons(self) -> List[Dict]:
        """Get all patient coupons"""
        response = self._request('GET', '/patient_coupons')
        return response.json()
    
    def create_patient_coupon(self, coupon_number: str, patient_name: str = None,
                             issue_date: str = None, expiry_date: str = None,
                             is_used: bool = False) -> Dict:
        """Create new patient coupon"""
        data = {
            'coupon_number': coupon_number,
            'patient_name': patient_name,
            'issue_date': issue_date or datetime.now().isoformat(),
            'expiry_date': expiry_date,
            'is_used': is_used
        }
        response = self._request('POST', '/patient_coupons', json=data)
        return response.json()
    
    # ==================== Activity Log Operations ====================
    
    def get_activity_logs(self, limit: int = 100, action_type: str = None) -> List[Dict]:
        """Get activity logs"""
        params = {'limit': limit}
        if action_type:
            params['action_type'] = action_type
        
        response = self._request('GET', '/activity_logs', params=params)
        return response.json()
    
    def create_activity_log(self, action_type: str, description: str, user: str = 'system') -> Dict:
        """Create new activity log entry"""
        data = {
            'action_type': action_type,
            'description': description,
            'user': user
        }
        response = self._request('POST', '/activity_logs', json=data)
        return response.json()
    
    # ==================== Statistics Operations ====================
    
    def get_inventory_statistics(self) -> Dict:
        """Get inventory statistics"""
        response = self._request('GET', '/statistics/inventory')
        return response.json()
    
    # ==================== Session Management (Compatibility) ====================
    
    @contextmanager
    def get_session(self):
        """
        Compatibility method for code that expects a session context.
        In client mode, this doesn't provide a real session but maintains API compatibility.
        """
        # Return self as a pseudo-session
        yield self
    
    def close(self):
        """Close HTTP session"""
        self.session.close()
