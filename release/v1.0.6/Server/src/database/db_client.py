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
        self.session.headers.update({
            'Content-Type': 'application/json; charset=utf-8',
            'Accept-Charset': 'utf-8'
        })
        
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
            response.encoding = 'utf-8'  # Force UTF-8 decoding
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
    
    def create_products_batch(self, products: List[Dict]) -> Dict:
        """Create multiple products in a single transaction (10-100x faster)"""
        response = self._request('POST', '/products/batch', json=products)
        return response.json()
    
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
                            po_reference: str = None, product_description: str = None,
                            warehouse_location: str = None, unit_price: float = None,
                            tax_rate: float = None, tax_amount: float = None,
                            total_without_tax: float = None, total_with_tax: float = None,
                            remaining_stock: float = None, purchase_date: str = None) -> Dict:
        """Create new purchase order"""
        data = {
            'product_id': product_id,
            'quantity': quantity,
            'po_reference': po_reference,
            'product_description': product_description,
            'warehouse_location': warehouse_location,
            'unit_price': unit_price,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total_without_tax': total_without_tax,
            'total_with_tax': total_with_tax,
            'remaining_stock': remaining_stock if remaining_stock is not None else quantity,
            'purchase_date': purchase_date or datetime.now().isoformat()
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
    
    def create_pharmacy(self, name: str, reference: str = None, trn: str = None,
                       contact_person: str = None, phone: str = None, 
                       email: str = None, notes: str = None) -> Dict:
        """Create new pharmacy"""
        data = {
            'name': name,
            'reference': reference,
            'trn': trn,
            'contact_person': contact_person,
            'phone': phone,
            'email': email,
            'notes': notes
        }
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
    
    def delete_distribution_location(self, location_id: int) -> bool:
        """Delete distribution location"""
        try:
            self._request('DELETE', f'/distribution_locations/{location_id}')
            return True
        except RuntimeError:
            return False
    
    def delete_medical_centre(self, centre_id: int) -> bool:
        """Delete medical centre"""
        try:
            self._request('DELETE', f'/medical_centres/{centre_id}')
            return True
        except RuntimeError:
            return False
    
    def delete_patient_coupon(self, coupon_id: int) -> bool:
        """Delete patient coupon"""
        try:
            self._request('DELETE', f'/patient_coupons/{coupon_id}')
            return True
        except RuntimeError:
            return False
    
    # ==================== Distribution Location Operations ====================
    
    def get_all_distribution_locations(self) -> List[Dict]:
        """Get all distribution locations"""
        response = self._request('GET', '/distribution_locations')
        return response.json()
    
    def create_distribution_location(self, name: str, reference: str = None,
                                    trn: str = None, pharmacy_id: int = None,
                                    address: str = None, contact_person: str = None,
                                    phone: str = None) -> Dict:
        """Create new distribution location"""
        data = {
            'name': name,
            'reference': reference,
            'trn': trn,
            'pharmacy_id': pharmacy_id,
            'address': address,
            'contact_person': contact_person,
            'phone': phone
        }
        response = self._request('POST', '/distribution_locations', json=data)
        return response.json()
    
    # ==================== Medical Centre Operations ====================
    
    def get_all_medical_centres(self) -> List[Dict]:
        """Get all medical centres"""
        response = self._request('GET', '/medical_centres')
        return response.json()
    
    def create_medical_centre(self, name: str, reference: str = None,
                             address: str = None, contact_person: str = None,
                             phone: str = None) -> Dict:
        """Create new medical centre"""
        data = {
            'name': name,
            'reference': reference,
            'address': address,
            'contact_person': contact_person,
            'phone': phone
        }
        response = self._request('POST', '/medical_centres', json=data)
        return response.json()
    
    # ==================== Patient Coupon Operations ====================
    
    def get_all_patient_coupons(self) -> List[Dict]:
        """Get all patient coupons"""
        response = self._request('GET', '/patient_coupons')
        return response.json()
    
    def create_patient_coupon(self, coupon_reference: str, patient_name: str = None,
                             cpr: str = None, quantity_pieces: int = None,
                             medical_centre_id: int = None, distribution_location_id: int = None,
                             product_id: int = None, verified: bool = False,
                             verification_reference: str = None, delivery_note_number: str = None,
                             grv_reference: str = None, date_received: str = None,
                             date_verified: str = None, notes: str = None) -> Dict:
        """Create new patient coupon"""
        data = {
            'coupon_reference': coupon_reference,
            'patient_name': patient_name,
            'cpr': cpr,
            'quantity_pieces': quantity_pieces,
            'medical_centre_id': medical_centre_id,
            'distribution_location_id': distribution_location_id,
            'product_id': product_id,
            'verified': verified,
            'verification_reference': verification_reference,
            'delivery_note_number': delivery_note_number,
            'grv_reference': grv_reference,
            'date_received': date_received or datetime.now().isoformat(),
            'date_verified': date_verified,
            'notes': notes
        }
        response = self._request('POST', '/patient_coupons', json=data)
        return response.json()
    
    def create_patient_coupons_batch(self, coupons: List[Dict]) -> Dict:
        """Create multiple patient coupons in a single transaction (10-100x faster)"""
        response = self._request('POST', '/patient_coupons/batch', json=coupons)
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
    
    # ==================== Generic CRUD Methods (Widget Compatibility) ====================
    
    def get_all(self, model_class):
        """
        Generic get_all method that routes to model-specific methods.
        Maintains compatibility with DatabaseManager interface.
        """
        from .models import (Product, PurchaseOrder, Pharmacy, DistributionLocation, 
                           MedicalCentre, PatientCoupon, Transaction)
        
        # Map model classes to their specific get_all methods
        model_map = {
            Product: self.get_all_products,
            PurchaseOrder: self.get_all_purchase_orders,
            Pharmacy: self.get_all_pharmacies,
            DistributionLocation: self.get_all_distribution_locations,
            MedicalCentre: self.get_all_medical_centres,
            PatientCoupon: self.get_all_patient_coupons,
            Transaction: self.get_all_transactions,
        }
        
        method = model_map.get(model_class)
        if method:
            # Convert dict responses to simple objects for compatibility
            results = method()
            # Return as-is (dicts) - widgets should handle both objects and dicts
            return results
        else:
            raise NotImplementedError(f"get_all not implemented for {model_class.__name__}")
    
    def add(self, record):
        """
        Generic add method that routes to model-specific create methods.
        Maintains compatibility with DatabaseManager interface.
        Note: This extracts data from the model object and sends to API.
        """
        from .models import (Product, PurchaseOrder, Pharmacy, DistributionLocation, 
                           MedicalCentre, PatientCoupon, Transaction)
        
        model_class = type(record)
        
        if model_class == Product:
            return self.create_product(
                name=record.name,
                reference=record.reference,
                unit=record.unit,
                description=record.description
            )
        elif model_class == PurchaseOrder:
            return self.create_purchase_order(
                product_id=record.product_id,
                quantity=record.quantity,
                po_reference=record.po_reference,
                product_description=record.product_description,
                warehouse_location=record.warehouse_location,
                unit_price=record.unit_price,
                tax_rate=record.tax_rate,
                tax_amount=record.tax_amount,
                total_without_tax=record.total_without_tax,
                total_with_tax=record.total_with_tax,
                remaining_stock=record.remaining_stock
            )
        elif model_class == Pharmacy:
            return self.create_pharmacy(
                name=record.name,
                reference=getattr(record, 'reference', None),
                trn=getattr(record, 'trn', None),
                contact_person=getattr(record, 'contact_person', None),
                phone=getattr(record, 'phone', None),
                email=getattr(record, 'email', None),
                notes=getattr(record, 'notes', None)
            )
        elif model_class == DistributionLocation:
            return self.create_distribution_location(
                name=record.name,
                reference=getattr(record, 'reference', None),
                trn=getattr(record, 'trn', None),
                pharmacy_id=record.pharmacy_id,
                address=getattr(record, 'address', None),
                contact_person=getattr(record, 'contact_person', None),
                phone=getattr(record, 'phone', None)
            )
        elif model_class == MedicalCentre:
            return self.create_medical_centre(
                name=record.name,
                reference=getattr(record, 'reference', None),
                address=getattr(record, 'address', None),
                contact_person=getattr(record, 'contact_person', None),
                phone=getattr(record, 'phone', None)
            )
        elif model_class == PatientCoupon:
            return self.create_patient_coupon(
                coupon_reference=record.coupon_reference,
                patient_name=getattr(record, 'patient_name', None),
                cpr=getattr(record, 'cpr', None),
                quantity_pieces=record.quantity_pieces,
                medical_centre_id=record.medical_centre_id,
                distribution_location_id=record.distribution_location_id,
                product_id=record.product_id,
                verified=getattr(record, 'verified', False),
                verification_reference=getattr(record, 'verification_reference', None),
                delivery_note_number=getattr(record, 'delivery_note_number', None),
                grv_reference=getattr(record, 'grv_reference', None),
                date_received=getattr(record, 'date_received', None),
                date_verified=getattr(record, 'date_verified', None),
                notes=getattr(record, 'notes', None)
            )
        elif model_class == Transaction:
            return self.create_transaction(
                product_id=record.product_id,
                quantity=record.quantity,
                transaction_type=record.transaction_type,
                transaction_date=getattr(record, 'transaction_date', None),
                pharmacy_id=getattr(record, 'pharmacy_id', None),
                distribution_location_id=getattr(record, 'distribution_location_id', None),
                medical_centre_id=getattr(record, 'medical_centre_id', None),
                notes=getattr(record, 'notes', None)
            )
        else:
            raise NotImplementedError(f"add not implemented for {model_class.__name__}")
    
    def delete(self, model_or_class, record_id=None):
        """
        Generic delete method that routes to model-specific delete methods.
        Maintains compatibility with DatabaseManager interface.
        
        Can be called as:
        - delete(Product, 5) - Delete by model class and ID
        - delete(product_object) - Delete by object (uses object.id)
        """
        from .models import (Product, PurchaseOrder, Pharmacy, DistributionLocation, 
                           MedicalCentre, PatientCoupon, Transaction)
        
        # Handle both delete(Model, id) and delete(object) signatures
        if record_id is None:
            # Called as delete(object)
            record = model_or_class
            model_class = type(record)
            record_id = record.id
        else:
            # Called as delete(Model, id)
            model_class = model_or_class
        
        # Map model classes to their specific delete methods
        delete_map = {
            Product: self.delete_product,
            PurchaseOrder: self.delete_purchase_order,
            Pharmacy: self.delete_pharmacy,
            DistributionLocation: self.delete_distribution_location,
            MedicalCentre: self.delete_medical_centre,
            PatientCoupon: self.delete_patient_coupon,
            Transaction: self.delete_transaction,
        }
        
        method = delete_map.get(model_class)
        if method:
            try:
                return method(record_id)
            except RuntimeError:
                return False
        else:
            raise NotImplementedError(f"delete not implemented for {model_class.__name__}")
