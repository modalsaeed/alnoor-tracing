"""
Alnoor Medical Services - API Server Test Script

This script tests the API server functionality by performing
common database operations and verifying responses.
"""

import requests
import sys
from datetime import datetime
from typing import Dict, Any


class APIServerTester:
    """Test the API server functionality"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append((name, passed))
        print(f"{status} - {name}")
        if message:
            print(f"   {message}")
    
    def test_health_check(self) -> bool:
        """Test server health endpoint"""
        try:
            response = self.session.get(f'{self.server_url}/health', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test("Health Check", True, f"Server version: {data.get('version')}")
                    return True
            self.log_test("Health Check", False, f"Unexpected response: {response.status_code}")
            return False
        except requests.exceptions.RequestException as e:
            self.log_test("Health Check", False, f"Connection error: {e}")
            return False
    
    def test_create_product(self) -> Dict[str, Any]:
        """Test creating a product"""
        try:
            test_product = {
                'name': 'Test Product API',
                'reference': f'TEST-API-{datetime.now().strftime("%H%M%S")}',
                'unit': 'pcs',
                'description': 'Created by API test script'
            }
            
            response = self.session.post(
                f'{self.server_url}/products',
                json=test_product,
                timeout=10
            )
            
            if response.status_code == 201:
                product = response.json()
                self.log_test("Create Product", True, f"Product ID: {product.get('id')}")
                return product
            else:
                self.log_test("Create Product", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Create Product", False, f"Error: {e}")
            return None
    
    def test_get_products(self) -> bool:
        """Test retrieving all products"""
        try:
            response = self.session.get(f'{self.server_url}/products', timeout=10)
            
            if response.status_code == 200:
                products = response.json()
                self.log_test("Get Products", True, f"Retrieved {len(products)} products")
                return True
            else:
                self.log_test("Get Products", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Products", False, f"Error: {e}")
            return False
    
    def test_update_product(self, product_id: int) -> bool:
        """Test updating a product"""
        try:
            update_data = {
                'description': f'Updated by test script at {datetime.now().strftime("%H:%M:%S")}'
            }
            
            response = self.session.put(
                f'{self.server_url}/products/{product_id}',
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Update Product", True)
                return True
            else:
                self.log_test("Update Product", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Update Product", False, f"Error: {e}")
            return False
    
    def test_delete_product(self, product_id: int) -> bool:
        """Test deleting a product"""
        try:
            response = self.session.delete(
                f'{self.server_url}/products/{product_id}',
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Delete Product", True)
                return True
            else:
                self.log_test("Delete Product", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Delete Product", False, f"Error: {e}")
            return False
    
    def test_create_pharmacy(self) -> bool:
        """Test creating a pharmacy"""
        try:
            test_pharmacy = {
                'name': f'Test Pharmacy {datetime.now().strftime("%H%M%S")}',
                'location': 'Test Location',
                'contact': '555-0123'
            }
            
            response = self.session.post(
                f'{self.server_url}/pharmacies',
                json=test_pharmacy,
                timeout=10
            )
            
            if response.status_code == 201:
                pharmacy = response.json()
                self.log_test("Create Pharmacy", True, f"Pharmacy ID: {pharmacy.get('id')}")
                return True
            else:
                self.log_test("Create Pharmacy", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create Pharmacy", False, f"Error: {e}")
            return False
    
    def test_statistics(self) -> bool:
        """Test getting statistics"""
        try:
            response = self.session.get(
                f'{self.server_url}/statistics/inventory',
                timeout=10
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "Get Statistics", 
                    True, 
                    f"Products: {stats.get('total_products')}, "
                    f"Transactions: {stats.get('total_transactions')}, "
                    f"Pharmacies: {stats.get('total_pharmacies')}"
                )
                return True
            else:
                self.log_test("Get Statistics", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Statistics", False, f"Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("Alnoor Medical Services - API Server Test")
        print("=" * 60)
        print()
        print(f"Testing server: {self.server_url}")
        print()
        
        # Test 1: Health check
        if not self.test_health_check():
            print("\n❌ Server is not accessible. Cannot continue tests.")
            return False
        
        print()
        
        # Test 2: Get products
        self.test_get_products()
        
        # Test 3: Create product
        product = self.test_create_product()
        
        # Test 4: Update product (if creation succeeded)
        if product:
            product_id = product.get('id')
            self.test_update_product(product_id)
            
            # Test 5: Delete product
            self.test_delete_product(product_id)
        
        # Test 6: Create pharmacy
        self.test_create_pharmacy()
        
        # Test 7: Get statistics
        self.test_statistics()
        
        print()
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            print("✅ All tests passed!")
            return True
        else:
            print(f"❌ {total - passed} test(s) failed")
            return False


def main():
    """Main test function"""
    # Get server URL from command line or use default
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        server_url = input("Enter server URL (e.g., http://192.168.1.10:5000): ").strip()
        if not server_url:
            server_url = "http://localhost:5000"
    
    print()
    
    # Run tests
    tester = APIServerTester(server_url)
    success = tester.run_all_tests()
    
    print()
    
    if success:
        print("🎉 API Server is working correctly!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check server logs for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
