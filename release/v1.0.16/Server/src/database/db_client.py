"""
Database Client for Remote API Access

This module provides HTTP client access to the database API server.
When configured in client mode, all database operations are forwarded
to the API server instead of accessing SQLite directly.
"""

import sys

# Check if requests module is available
try:
    import requests
except ImportError:
    print("ERROR: 'requests' module not found!")
    print("\nThe API client mode requires the 'requests' package.")
    print("Please install it with: pip install requests")
    print("\nOr disable API client mode in config.ini:")
    print("  [server]")
    print("  mode = local")
    sys.exit(1)

from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class DatabaseClient:
    def create_backup(self) -> str:
        """Create a manual backup via the API server and return the backup path. Raises detailed error if server fails."""
        try:
            response = self._request('POST', '/backup/manual')
            data = response.json()
            # The API returns {'path': ...} or similar
            if isinstance(data, dict) and 'path' in data:
                return data['path']
            # Fallback: return the whole response as string
            return str(data)
        except RuntimeError as e:
            # Try to extract error message from server response if available
            if hasattr(e, 'args') and e.args:
                msg = e.args[0]
                # If the error message contains a server response, try to extract JSON
                import re
                import json
                match = re.search(r'Response:\s*(\{.*\})', msg)
                if match:
                    try:
                        err_json = json.loads(match.group(1))
                        if 'message' in err_json:
                            raise RuntimeError(f"API backup error: {err_json['message']}")
                    except Exception:
                        pass
                raise RuntimeError(f"API backup error: {msg}")
            raise
    # ==================== Backup Operations ====================
    def list_backups(self) -> dict:
        """List available database backups from the API server (returns dict with 'weekly' and 'manual' keys)"""
        response = self._request('GET', '/backup/list')
        return response.json()

    # ==================== Delivery Note Operations ====================
    def get_all_delivery_notes(self) -> list:
        """Get all delivery notes"""
        response = self._request('GET', '/delivery_notes')
        return response.json()

    def get_delivery_note(self, note_id: int) -> dict:
        """Get delivery note by ID"""
        response = self._request('GET', f'/delivery_notes/{note_id}')
        return response.json()

    def create_delivery_note(self, **kwargs) -> dict:
        """Create new delivery note"""
        response = self._request('POST', '/delivery_notes', json=kwargs)
        return response.json()

    def update_delivery_note(self, note_id: int, **kwargs) -> dict:
        """Update existing delivery note"""
        response = self._request('PUT', f'/delivery_notes/{note_id}', json=kwargs)
        return response.json()

    def delete_delivery_note(self, note_id: int) -> dict:
        """Delete delivery note"""
        response = self._request('DELETE', f'/delivery_notes/{note_id}')
        return response.json()
    def update_medical_centre(self, centre_id: int, **kwargs) -> dict:
        """Update existing medical centre"""
        response = self._request('PUT', f'/medical_centres/{centre_id}', json=kwargs)
        return response.json()
    
    def update_distribution_location(self, location_id: int, **kwargs) -> dict:
        """Update existing distribution location"""
        response = self._request('PUT', f'/distribution_locations/{location_id}', json=kwargs)
        return response.json()
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
    
    # ==================== Purchase (Supplier Invoice) Operations ====================
    
    def get_all_purchases(self) -> List[Dict]:
        """Get all supplier purchases"""
        response = self._request('GET', '/purchases')
        return response.json()
    
    def get_purchase(self, purchase_id: int) -> Optional[Dict]:
        """Get purchase by ID"""
        try:
            response = self._request('GET', f'/purchases/{purchase_id}')
            return response.json()
        except RuntimeError:
            return None
    
    def create_purchase(self, invoice_number: str, purchase_order_id: int,
                       product_id: int, quantity: int, unit_price: float,
                       total_price: float, remaining_stock: int = None,
                       purchase_date: str = None, supplier_name: str = None,
                       notes: str = None) -> Dict:
        """Create new supplier purchase"""
        # Defensive: ensure purchase_date is always a string
        if purchase_date is not None and not isinstance(purchase_date, str):
            purchase_date = purchase_date.isoformat()
        data = {
            'invoice_number': invoice_number,
            'purchase_order_id': purchase_order_id,
            'product_id': product_id,
            'quantity': quantity,
            'remaining_stock': remaining_stock if remaining_stock is not None else quantity,
            'unit_price': unit_price,
            'total_price': total_price,
            'purchase_date': purchase_date or datetime.now().isoformat(),
            'supplier_name': supplier_name,
            'notes': notes
        }
        response = self._request('POST', '/purchases', json=data)
        return response.json()
    
    def update_purchase(self, purchase_id: int, **kwargs) -> Dict:
        """Update existing purchase"""
        response = self._request('PUT', f'/purchases/{purchase_id}', json=kwargs)
        return response.json()
    
    def delete_purchase(self, purchase_id: int) -> bool:
        """Delete purchase"""
        try:
            self._request('DELETE', f'/purchases/{purchase_id}')
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
    
    def create_transaction(self, purchase_id: int, product_id: int, quantity: float, 
                          distribution_location_id: int = None, transaction_date: str = None,
                          transaction_reference: str = None, notes: str = None) -> Dict:
        """Create new transaction (API mode)"""
        data = {
            'purchase_id': purchase_id,
            'product_id': product_id,
            'quantity': quantity,
            'distribution_location_id': distribution_location_id,
            'transaction_date': transaction_date or datetime.now().isoformat(),
            'notes': notes
        }
        if transaction_reference:
            data['transaction_reference'] = transaction_reference
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
        from datetime import datetime
        # Ensure date_received and date_verified are ISO strings
        dr = date_received or datetime.now().isoformat()
        if isinstance(dr, datetime):
            dr = dr.isoformat()
        dv = date_verified
        if isinstance(dv, datetime):
            dv = dv.isoformat()
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
            'date_received': dr,
            'date_verified': dv,
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
    
    def get_database_info(self) -> Dict:
        """Get database information for status bar (API client version)"""
        # For API client, we can't get actual DB path/size, so return approximations
        try:
            # Get counts from server
            products = self.get_all(Product) if hasattr(self, 'get_all') else []
            coupons = self.get_all(PatientCoupon) if hasattr(self, 'get_all') else []
            pos = self.get_all(PurchaseOrder) if hasattr(self, 'get_all') else []
            
            verified_count = sum(1 for c in coupons if isinstance(c, dict) and c.get('verified', False))
            
            return {
                'db_path': f'API Server: {self.server_url}',
                'db_size_mb': 0.0,  # Not available in client mode
                'products_count': len(products),
                'purchase_orders_count': len(pos),
                'distribution_locations_count': 0,
                'medical_centres_count': 0,
                'coupons_count': len(coupons),
                'verified_coupons_count': verified_count,
                'transactions_count': 0,
                'activity_logs_count': 0,
            }
        except Exception:
            # Fallback if counts fail
            return {
                'db_path': f'API Server: {self.server_url}',
                'db_size_mb': 0.0,
                'products_count': 0,
                'purchase_orders_count': 0,
                'distribution_locations_count': 0,
                'medical_centres_count': 0,
                'coupons_count': 0,
                'verified_coupons_count': 0,
                'transactions_count': 0,
                'activity_logs_count': 0,
            }
    
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
        from .models import (Product, PurchaseOrder, Purchase, Pharmacy, DistributionLocation, 
                           MedicalCentre, PatientCoupon, Transaction)
        
        # Map model classes to their specific get_all methods
        model_map = {
            Product: self.get_all_products,
            PurchaseOrder: self.get_all_purchase_orders,
            Purchase: self.get_all_purchases,
            Pharmacy: self.get_all_pharmacies,
            DistributionLocation: self.get_all_distribution_locations,
            MedicalCentre: self.get_all_medical_centres,
            PatientCoupon: self.get_all_patient_coupons,
            Transaction: self.get_all_transactions,
        }
        
        method = model_map.get(model_class)
        if method:
            results = method()
            if results is None:
                return []
            return results
        else:
            raise NotImplementedError(f"get_all not implemented for {model_class.__name__}")
    
    def add(self, record):
        """
        Generic add method that routes to model-specific create methods.
        Maintains compatibility with DatabaseManager interface.
        Accepts both ORM objects and dicts.
        Only creates new records (must not have an id).
        """
        from .models import (Product, PurchaseOrder, Purchase, Pharmacy, DistributionLocation, 
                           MedicalCentre, PatientCoupon, Transaction)
        # Accept dicts as well as ORM objects
        if isinstance(record, dict):
            model_class = record.get('__model_class__')
            if not model_class:
                # Fallback: guess by keys
                if 'unit' in record and 'reference' in record and 'name' in record:
                    model_class = Product
                elif 'po_reference' in record and 'product_id' in record:
                    model_class = PurchaseOrder
                elif 'invoice_number' in record and 'purchase_order_id' in record:
                    model_class = Purchase
                elif 'trn' in record and 'name' in record and 'contact_person' in record:
                    model_class = Pharmacy
                elif 'pharmacy_id' in record and 'name' in record and 'address' in record:
                    model_class = DistributionLocation
                elif 'address' in record and 'contact_person' in record and 'phone' in record:
                    model_class = MedicalCentre
                elif 'coupon_reference' in record and 'product_id' in record:
                    model_class = PatientCoupon
                elif 'transaction_type' in record and 'product_id' in record:
                    model_class = Transaction
                else:
                    raise NotImplementedError("add not implemented for dict with unknown structure")
            # If record has an id, treat as update, not add
            if record.get('id') is not None:
                raise ValueError("add() called with record that already has an id; use update() instead")
            from types import SimpleNamespace
            record_obj = SimpleNamespace(**record)
            record = record_obj
        else:
            model_class = type(record)
            if hasattr(record, 'id') and getattr(record, 'id', None) is not None:
                raise ValueError("add() called with record that already has an id; use update() instead")
        # ...existing code for model_class dispatch...
        if model_class == Product:
            return self.create_product(
                name=getattr(record, 'name', None),
                reference=getattr(record, 'reference', None),
                unit=getattr(record, 'unit', None),
                description=getattr(record, 'description', None)
            )
        elif model_class == PurchaseOrder:
            return self.create_purchase_order(
                product_id=getattr(record, 'product_id', None),
                quantity=getattr(record, 'quantity', None),
                po_reference=getattr(record, 'po_reference', None),
                product_description=getattr(record, 'product_description', None),
                warehouse_location=getattr(record, 'warehouse_location', None),
                unit_price=getattr(record, 'unit_price', None),
                tax_rate=getattr(record, 'tax_rate', None),
                tax_amount=getattr(record, 'tax_amount', None),
                total_without_tax=getattr(record, 'total_without_tax', None),
                total_with_tax=getattr(record, 'total_with_tax', None),
                remaining_stock=getattr(record, 'remaining_stock', None)
            )
        elif model_class == Purchase:
            return self.create_purchase(
                invoice_number=getattr(record, 'invoice_number', None),
                purchase_order_id=getattr(record, 'purchase_order_id', None),
                product_id=getattr(record, 'product_id', None),
                quantity=getattr(record, 'quantity', None),
                unit_price=float(getattr(record, 'unit_price', 0)),
                total_price=float(getattr(record, 'total_price', 0)),
                remaining_stock=getattr(record, 'remaining_stock', None),
                purchase_date=getattr(record, 'purchase_date', None),
                supplier_name=getattr(record, 'supplier_name', None),
                notes=getattr(record, 'notes', None)
            )
        elif model_class == Pharmacy:
            return self.create_pharmacy(
                name=getattr(record, 'name', None),
                reference=getattr(record, 'reference', None),
                trn=getattr(record, 'trn', None),
                contact_person=getattr(record, 'contact_person', None),
                phone=getattr(record, 'phone', None),
                email=getattr(record, 'email', None),
                notes=getattr(record, 'notes', None)
            )
        elif model_class == DistributionLocation:
            return self.create_distribution_location(
                name=getattr(record, 'name', None),
                reference=getattr(record, 'reference', None),
                trn=getattr(record, 'trn', None),
                pharmacy_id=getattr(record, 'pharmacy_id', None),
                address=getattr(record, 'address', None),
                contact_person=getattr(record, 'contact_person', None),
                phone=getattr(record, 'phone', None)
            )
        elif model_class == MedicalCentre:
            return self.create_medical_centre(
                name=getattr(record, 'name', None),
                reference=getattr(record, 'reference', None),
                address=getattr(record, 'address', None),
                contact_person=getattr(record, 'contact_person', None),
                phone=getattr(record, 'phone', None)
            )
        elif model_class == PatientCoupon:
            return self.create_patient_coupon(
                coupon_reference=getattr(record, 'coupon_reference', None),
                patient_name=getattr(record, 'patient_name', None),
                cpr=getattr(record, 'cpr', None),
                quantity_pieces=getattr(record, 'quantity_pieces', None),
                medical_centre_id=getattr(record, 'medical_centre_id', None),
                distribution_location_id=getattr(record, 'distribution_location_id', None),
                product_id=getattr(record, 'product_id', None),
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
                purchase_id=getattr(record, 'purchase_id', None),
                product_id=getattr(record, 'product_id', None),
                quantity=getattr(record, 'quantity', None),
                distribution_location_id=getattr(record, 'distribution_location_id', None),
                transaction_date=getattr(record, 'transaction_date', None),
                transaction_reference=getattr(record, 'transaction_reference', None),
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
        from .models import (Product, PurchaseOrder, Purchase, Pharmacy, DistributionLocation, 
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
            Purchase: self.delete_purchase,
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

    def update(self, record):
        """Update a record (generic, for widgets/dialogs). Handles PatientCoupon datetime serialization."""
        # Defensive: handle dict/ORM and datetime serialization for PatientCoupon
        import inspect
        from datetime import datetime
        model_name = None
        if hasattr(record, '__tablename__'):
            model_name = getattr(record, '__tablename__', None)
        elif isinstance(record, dict) and 'id' in record:
            # Try to infer model from dict keys
            if 'coupon_reference' in record and 'date_received' in record:
                model_name = 'patient_coupon'
        # PatientCoupon special handling
        if model_name == 'patient_coupon' or (isinstance(record, dict) and 'coupon_reference' in record and 'date_received' in record):
            # Ensure all datetime fields are ISO strings
            for dt_field in ['date_received', 'date_verified']:
                if dt_field in record and isinstance(record[dt_field], datetime):
                    record[dt_field] = record[dt_field].isoformat()
        # Use id for update
        record_id = record['id'] if isinstance(record, dict) else getattr(record, 'id', None)
        if not record_id:
            raise ValueError('Record must have an id for update')
        # Remove id from payload for API update
        payload = dict(record) if isinstance(record, dict) else {k: v for k, v in record.__dict__.items() if not k.startswith('_')}
        payload.pop('id', None)
        # Remove SQLAlchemy state if present
        payload.pop('_sa_instance_state', None)
        # PatientCoupon: remove created_at/updated_at if present (read-only)
        for ro_field in ['created_at', 'updated_at']:
            payload.pop(ro_field, None)
        # Route by model
        if model_name == 'patient_coupon':
            response = self._request('PUT', f'/patient_coupons/{record_id}', json=payload)
            return response.json()
        # Fallback: try to guess endpoint from class name
        class_name = record.__class__.__name__ if not isinstance(record, dict) else None
        if class_name == 'MedicalCentre' or model_name == 'medical_centre':
            response = self._request('PUT', f'/medical_centres/{record_id}', json=payload)
            return response.json()
        if class_name == 'DistributionLocation' or model_name == 'distribution_location':
            response = self._request('PUT', f'/distribution_locations/{record_id}', json=payload)
            return response.json()
        if class_name == 'Pharmacy' or model_name == 'pharmacy':
            response = self._request('PUT', f'/pharmacies/{record_id}', json=payload)
            return response.json()
        if class_name == 'Product' or model_name == 'product':
            response = self._request('PUT', f'/products/{record_id}', json=payload)
            return response.json()
        if class_name == 'PurchaseOrder' or model_name == 'purchase_order':
            response = self._request('PUT', f'/purchase_orders/{record_id}', json=payload)
            return response.json()
        if class_name == 'Purchase' or model_name == 'purchase':
            response = self._request('PUT', f'/purchases/{record_id}', json=payload)
            return response.json()
        # Fallback: raise error
        raise NotImplementedError(f'Update not implemented for {class_name or model_name}')
        """
        Generic update method that routes to model-specific update methods.
        Maintains compatibility with DatabaseManager interface.
        Accepts both ORM objects and dicts.
        """
        from .models import (Product, PurchaseOrder, Purchase, Pharmacy, DistributionLocation, 
                           MedicalCentre, PatientCoupon, Transaction)
        if isinstance(record, dict):
            model_class = record.get('__model_class__')
            if not model_class:
                # Fallback: guess by keys
                if 'unit' in record and 'reference' in record and 'name' in record:
                    model_class = Product
                elif 'po_reference' in record and 'product_id' in record:
                    model_class = PurchaseOrder
                elif 'invoice_number' in record and 'purchase_order_id' in record:
                    model_class = Purchase
                elif 'pharmacy_id' in record and 'name' in record and 'address' in record:
                    model_class = DistributionLocation
                elif 'trn' in record and 'name' in record and 'contact_person' in record:
                    model_class = Pharmacy
                elif 'address' in record and 'contact_person' in record and 'phone' in record:
                    model_class = MedicalCentre
                elif 'coupon_reference' in record and 'product_id' in record:
                    model_class = PatientCoupon
                elif 'transaction_type' in record and 'product_id' in record:
                    model_class = Transaction
                else:
                    raise NotImplementedError("update not implemented for dict with unknown structure")
            record_id = record.get('id')
            update_data = record.copy()
            update_data.pop('__model_class__', None)
            update_data.pop('id', None)
        else:
            model_class = type(record)
            record_id = getattr(record, 'id', None)
            update_data = {k: getattr(record, k) for k in dir(record) if not k.startswith('_') and not callable(getattr(record, k))}
            update_data.pop('id', None)
        # Route to model-specific update method
        if model_class == Product:
            return self.update_product(record_id, **update_data)
        elif model_class == PurchaseOrder:
            return self.update_purchase_order(record_id, **update_data)
        elif model_class == Purchase:
            return self.update_purchase(record_id, **update_data)
        elif model_class == Pharmacy:
            return self.update_pharmacy(record_id, **update_data)
        elif model_class == DistributionLocation:
            return self.update_distribution_location(record_id, **update_data)
        elif model_class == MedicalCentre:
            return self.update_medical_centre(record_id, **update_data)
        elif model_class == PatientCoupon:
            # No update endpoint implemented for PatientCoupon
            raise NotImplementedError("update not implemented for PatientCoupon")
        elif model_class == Transaction:
            # No update endpoint implemented for Transaction
            raise NotImplementedError("update not implemented for Transaction")
        else:
            raise NotImplementedError(f"update not implemented for {model_class.__name__}")