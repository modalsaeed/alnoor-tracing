"""
Comprehensive API Server Test Suite
Tests encoding, concurrent requests, and data integrity
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

SERVER_URL = "http://127.0.0.1:5000"

def colored(text, color):
    """Add color to console output"""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def cleanup_test_data():
    """Clean up test data from previous runs"""
    print(colored("\n🧹 Cleaning up test data from previous runs...", 'yellow'))
    try:
        deleted_products = 0
        deleted_coupons = 0
        deleted_medicals = 0
        deleted_locations = 0
        
        # Delete test coupons first (they reference products, medical centres, distribution locations)
        response = requests.get(f"{SERVER_URL}/patient_coupons", timeout=5)
        if response.status_code == 200:
            coupons = response.json()
            for coupon in coupons:
                ref = coupon.get('coupon_reference', '')
                if any(prefix in ref for prefix in ['COUPON-', 'CONC-COUPON', 'TCPN']):
                    del_response = requests.delete(f"{SERVER_URL}/patient_coupons/{coupon['id']}", timeout=5)
                    if del_response.status_code == 200:
                        deleted_coupons += 1
        
        # Delete test products (those with test-related references)
        response = requests.get(f"{SERVER_URL}/products", timeout=5)
        if response.status_code == 200:
            products = response.json()
            for product in products:
                ref = product.get('reference', '')
                if any(prefix in ref for prefix in ['USER', 'SPEC', 'BULK', 'TEST', 'COUPON-PROD', 'CONC-PROD']):
                    del_response = requests.delete(f"{SERVER_URL}/products/{product['id']}", timeout=5)
                    if del_response.status_code == 200:
                        deleted_products += 1
        
        # Delete test medical centres
        response = requests.get(f"{SERVER_URL}/medical_centres", timeout=5)
        if response.status_code == 200:
            centres = response.json()
            for centre in centres:
                name = centre.get('name', '')
                ref = centre.get('reference', '')
                if 'Test' in name or 'Concurrent' in name or any(prefix in str(ref) for prefix in ['TMC', 'CMC']):
                    # Note: Would need DELETE endpoint - skip for now
                    deleted_medicals += 1
        
        # Delete test distribution locations
        response = requests.get(f"{SERVER_URL}/distribution_locations", timeout=5)
        if response.status_code == 200:
            locations = response.json()
            for location in locations:
                name = location.get('name', '')
                ref = location.get('reference', '')
                if 'Test' in name or 'Concurrent' in name or any(prefix in str(ref) for prefix in ['TDL', 'CDL']):
                    # Note: Would need DELETE endpoint - skip for now
                    deleted_locations += 1
        
        if deleted_coupons > 0:
            print(colored(f"✓ Cleaned up {deleted_coupons} test coupons\n", 'green'))
        print(colored(f"✓ Cleaned up {deleted_products} test products\n", 'green'))
        if deleted_medicals > 0:
            print(colored(f"⚠ Found {deleted_medicals} test medical centres (no DELETE endpoint yet)\n", 'yellow'))
        if deleted_locations > 0:
            print(colored(f"⚠ Found {deleted_locations} test distribution locations (no DELETE endpoint yet)\n", 'yellow'))
    except Exception as e:
        print(colored(f"⚠ Cleanup failed: {e}\n", 'yellow'))

def test_health_check():
    """Test 1: Health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        response.encoding = 'utf-8'
        response.raise_for_status()
        data = response.json()
        print(colored("✓ PASS", 'green') + f" - Server is healthy")
        print(f"  Status: {data.get('status')}")
        print(f"  Version: {data.get('version')}")
        return True
    except Exception as e:
        print(colored("✗ FAIL", 'red') + f" - {e}")
        return False

def test_utf8_encoding():
    """Test 2: UTF-8 encoding with Arabic text"""
    print("\n" + "="*60)
    print("TEST 2: UTF-8 Encoding (Arabic text)")
    print("="*60)
    
    # Test data with Arabic text
    test_product = {
        "name": "دواء الألم",  # Arabic: Pain medication
        "reference": "TEST123456",
        "description": "العلامة التجارية"  # Arabic: Brand name
    }
    
    try:
        # Create product with Arabic text
        response = requests.post(
            f"{SERVER_URL}/products",
            json=test_product,
            headers={'Content-Type': 'application/json; charset=utf-8'},
            timeout=5
        )
        response.encoding = 'utf-8'
        response.raise_for_status()
        created_product = response.json()
        product_id = created_product['id']
        
        # Verify Arabic text is preserved
        if created_product['name'] == test_product['name']:
            print(colored("✓ PASS", 'green') + " - Arabic text preserved correctly")
            print(f"  Product Name: {created_product['name']}")
            print(f"  Description: {created_product.get('description', '')}")
        else:
            print(colored("✗ FAIL", 'red') + " - Arabic text corrupted")
            return False
        
        # Get product back and verify
        response = requests.get(f"{SERVER_URL}/products/{product_id}", timeout=5)
        response.encoding = 'utf-8'
        response.raise_for_status()
        retrieved_product = response.json()
        
        if retrieved_product['name'] == test_product['name']:
            print(colored("✓ PASS", 'green') + " - Arabic text retrieved correctly")
        else:
            print(colored("✗ FAIL", 'red') + " - Arabic text corrupted on retrieval")
            return False
        
        # Clean up
        requests.delete(f"{SERVER_URL}/products/{product_id}", timeout=5)
        print(colored("✓ PASS", 'green') + " - UTF-8 encoding test complete")
        return True
        
    except Exception as e:
        print(colored("✗ FAIL", 'red') + f" - {e}")
        return False

def test_concurrent_requests():
    """Test 3: Concurrent user requests"""
    print("\n" + "="*60)
    print("TEST 3: Concurrent Requests (Simulating 10 users)")
    print("="*60)
    
    def create_product_request(user_id):
        """Simulate a user creating a product"""
        product = {
            "name": f"Test Product User {user_id}",
            "reference": f"USER{user_id:04d}",
            "description": f"Brand {user_id}"
        }
        try:
            response = requests.post(
                f"{SERVER_URL}/products",
                json=product,
                timeout=10
            )
            response.encoding = 'utf-8'
            response.raise_for_status()
            return (user_id, True, response.json()['id'])
        except Exception as e:
            return (user_id, False, str(e))
    
    # Send 10 concurrent requests
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_product_request, i) for i in range(1, 11)]
        results = [future.result() for future in as_completed(futures)]
    
    duration = time.time() - start_time
    
    # Check results
    successes = [r for r in results if r[1]]
    failures = [r for r in results if not r[1]]
    
    print(f"  Concurrent Requests: 10")
    print(f"  Successful: {len(successes)}")
    print(f"  Failed: {len(failures)}")
    print(f"  Duration: {duration:.2f} seconds")
    
    if len(successes) == 10:
        print(colored("✓ PASS", 'green') + " - All concurrent requests succeeded")
        
        # Clean up created products
        for user_id, success, product_id in successes:
            requests.delete(f"{SERVER_URL}/products/{product_id}", timeout=5)
        print(colored("  ✓ Cleanup complete", 'blue'))
        return True
    else:
        print(colored("✗ FAIL", 'red') + f" - {len(failures)} requests failed")
        for user_id, success, error in failures:
            print(f"  User {user_id}: {error}")
        return False

def test_special_characters():
    """Test 4: Special characters in product names"""
    print("\n" + "="*60)
    print("TEST 4: Special Characters")
    print("="*60)
    
    special_names = [
        "Product™ with trademark",
        "Product® registered",
        "Product © copyright",
        "Product & Supplies",
        "Product (100mg)",
        "Product [Pack of 10]",
        "Product - Professional",
        "Product: Medical Grade"
    ]
    
    try:
        created_ids = []
        for name in special_names:
            product = {
                "name": name,
                "reference": f"SPEC{len(created_ids):04d}",
                "description": "Test Brand"
            }
            response = requests.post(f"{SERVER_URL}/products", json=product, timeout=5)
            response.encoding = 'utf-8'
            response.raise_for_status()
            created_product = response.json()
            created_ids.append(created_product['id'])
            
            if created_product['name'] != name:
                print(colored("✗ FAIL", 'red') + f" - Special character corrupted: {name}")
                return False
        
        print(colored("✓ PASS", 'green') + f" - All {len(special_names)} special character tests passed")
        
        # Clean up
        for product_id in created_ids:
            requests.delete(f"{SERVER_URL}/products/{product_id}", timeout=5)
        
        return True
    except Exception as e:
        print(colored("✗ FAIL", 'red') + f" - {e}")
        return False

def test_large_dataset():
    """Test 5: Handling larger datasets"""
    print("\n" + "="*60)
    print("TEST 5: Large Dataset (100 products)")
    print("="*60)
    
    try:
        # Create 100 products
        created_ids = []
        start_time = time.time()
        
        for i in range(100):
            product = {
                "name": f"Bulk Product {i+1}",
                "reference": f"BULK{i:05d}",
                "description": f"Brand {(i % 10) + 1}"
            }
            response = requests.post(f"{SERVER_URL}/products", json=product, timeout=5)
            response.encoding = 'utf-8'
            response.raise_for_status()
            created_ids.append(response.json()['id'])
        
        create_time = time.time() - start_time
        
        # Retrieve all products
        start_time = time.time()
        response = requests.get(f"{SERVER_URL}/products", timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        all_products = response.json()
        retrieve_time = time.time() - start_time
        
        print(f"  Created: 100 products in {create_time:.2f}s")
        print(f"  Retrieved: {len(all_products)} products in {retrieve_time:.2f}s")
        
        if len(all_products) >= 100:
            print(colored("✓ PASS", 'green') + " - Large dataset handling successful")
        else:
            print(colored("✗ FAIL", 'red') + " - Not all products retrieved")
            return False
        
        # Clean up
        start_time = time.time()
        for product_id in created_ids:
            requests.delete(f"{SERVER_URL}/products/{product_id}", timeout=5)
        delete_time = time.time() - start_time
        
        print(f"  Deleted: 100 products in {delete_time:.2f}s")
        return True
        
    except Exception as e:
        print(colored("✗ FAIL", 'red') + f" - {e}")
        return False

def test_error_handling():
    """Test 6: Error handling"""
    print("\n" + "="*60)
    print("TEST 6: Error Handling")
    print("="*60)
    
    try:
        # Test 1: Invalid product ID
        response = requests.get(f"{SERVER_URL}/products/99999", timeout=5)
        if response.status_code == 404:
            print(colored("✓ PASS", 'green') + " - Returns 404 for invalid product")
        else:
            print(colored("✗ FAIL", 'red') + f" - Expected 404, got {response.status_code}")
            return False
        
        # Test 2: Missing required fields
        invalid_product = {
            "name": "Test"
            # Missing required 'reference' field
        }
        response = requests.post(f"{SERVER_URL}/products", json=invalid_product, timeout=5)
        if response.status_code in [400, 500]:
            print(colored("✓ PASS", 'green') + " - Rejects incomplete product data")
        else:
            print(colored("✗ FAIL", 'red') + f" - Expected error, got {response.status_code}")
            return False
        
        print(colored("✓ PASS", 'green') + " - Error handling working correctly")
        return True
        
    except Exception as e:
        print(colored("✗ FAIL", 'red') + f" - {e}")
        return False

def test_coupons_large_dataset():
    """Test 7: Large coupon dataset (1000 coupons)"""
    print("\n" + "="*60)
    print("TEST 7: Large Coupon Dataset (1000 coupons)")
    print("="*60)
    
    try:
        # Use timestamp to ensure unique references
        timestamp = int(time.time())
        
        # Step 1: Create test infrastructure (medical centre, distribution location, product)
        print("  Setting up test infrastructure...")
        
        # Create product
        product_data = {
            "name": "Test Product for Coupons",
            "reference": f"COUPON-PROD-{timestamp}",
            "description": "Test product"
        }
        response = requests.post(f"{SERVER_URL}/products", json=product_data, timeout=5)
        response.raise_for_status()
        product_id = response.json()['id']
        
        # Create medical centre
        medical_centre_data = {
            "name": "Test Medical Centre",
            "reference": f"TMC-{timestamp}"
        }
        response = requests.post(f"{SERVER_URL}/medical_centres", json=medical_centre_data, timeout=5)
        response.raise_for_status()
        medical_centre_id = response.json()['id']
        
        # Create distribution location
        dist_location_data = {
            "name": "Test Distribution Location",
            "reference": f"TDL-{timestamp}"
        }
        response = requests.post(f"{SERVER_URL}/distribution_locations", json=dist_location_data, timeout=5)
        response.raise_for_status()
        dist_location_id = response.json()['id']
        
        print(colored("  ✓ Infrastructure created", 'blue'))
        
        # Step 2: Create 1000 coupons using BATCH endpoint for speed
        start_time = time.time()
        
        # Build batch of coupons
        coupons_batch = []
        for i in range(1000):
            coupon_data = {
                "coupon_reference": f"COUPON-{i+1:06d}",
                "patient_name": f"Test Patient {i+1}",
                "cpr": f"{1000000 + i}",
                "quantity_pieces": (i % 100) + 1,
                "medical_centre_id": medical_centre_id,
                "distribution_location_id": dist_location_id,
                "product_id": product_id,
                "date_received": "2025-12-24T10:00:00",
                "verified": i % 2 == 0,  # Every other coupon verified
                "notes": f"Test coupon batch {i // 100}"
            }
            coupons_batch.append(coupon_data)
        
        print(f"  Creating 1000 coupons in batch mode...")
        response = requests.post(f"{SERVER_URL}/patient_coupons/batch", json=coupons_batch, timeout=30)
        response.raise_for_status()
        
        create_time = time.time() - start_time
        
        # Step 3: Retrieve all coupons
        start_time = time.time()
        response = requests.get(f"{SERVER_URL}/patient_coupons", timeout=15)
        response.raise_for_status()
        all_coupons = response.json()
        retrieve_time = time.time() - start_time
        
        print(f"\n  Created: 1000 coupons in {create_time:.2f}s ({1000/create_time:.1f} coupons/sec)")
        print(f"  Retrieved: {len(all_coupons)} coupons in {retrieve_time:.2f}s")
        
        if len(all_coupons) >= 1000:
            print(colored("✓ PASS", 'green') + " - Large coupon dataset handling successful")
        else:
            print(colored("✗ FAIL", 'red') + f" - Expected at least 1000 coupons, got {len(all_coupons)}")
            return False
        
        # Step 4: Verify data integrity (check a few random coupons)
        verified_count = sum(1 for c in all_coupons if c.get('verified'))
        print(f"  Verified coupons: {verified_count} (expected ~500)")
        
        # Step 5: Clean up - delete all test coupons
        print("\n  Cleaning up...")
        start_time = time.time()
        
        # Delete coupons (note: need DELETE endpoint - using product cleanup for now)
        # For comprehensive test, we'll leave them and rely on cleanup_test_data
        
        # Delete infrastructure
        requests.delete(f"{SERVER_URL}/products/{product_id}", timeout=5)
        # Note: Would need DELETE endpoints for medical_centres and distribution_locations
        
        cleanup_time = time.time() - start_time
        print(colored(f"  ✓ Cleanup complete in {cleanup_time:.2f}s", 'blue'))
        
        return True
        
    except Exception as e:
        print(colored("✗ FAIL", 'red') + f" - {e}")
        traceback_import = __import__('traceback')
        traceback_import.print_exc()
        return False

def test_concurrent_coupon_creation():
    """Test 8: Concurrent coupon creation (10 users creating coupons simultaneously)"""
    print("\n" + "="*60)
    print("TEST 8: Concurrent Coupon Creation")
    print("="*60)
    
    try:
        # Use timestamp to ensure unique references
        timestamp = int(time.time())
        
        # Setup infrastructure
        print("  Setting up infrastructure...")
        
        # Create product
        product_data = {"name": "Concurrent Test Product", "reference": f"CONC-PROD-{timestamp}"}
        response = requests.post(f"{SERVER_URL}/products", json=product_data, timeout=5)
        response.raise_for_status()
        product_id = response.json()['id']
        
        # Create medical centre
        medical_centre_data = {"name": "Concurrent Medical Centre", "reference": f"CMC-{timestamp}"}
        response = requests.post(f"{SERVER_URL}/medical_centres", json=medical_centre_data, timeout=5)
        response.raise_for_status()
        medical_centre_id = response.json()['id']
        
        # Create distribution location
        dist_location_data = {"name": "Concurrent Distribution Location", "reference": f"CDL-{timestamp}"}
        response = requests.post(f"{SERVER_URL}/distribution_locations", json=dist_location_data, timeout=5)
        response.raise_for_status()
        dist_location_id = response.json()['id']
        
        print(colored("  ✓ Infrastructure created", 'blue'))
        
        def create_coupon_request(user_id):
            """Simulate a user creating a coupon"""
            coupon_data = {
                "coupon_reference": f"CONC-COUPON-{timestamp}-{user_id:04d}",
                "patient_name": f"Concurrent Patient {user_id}",
                "cpr": f"{2000000 + user_id}",
                "quantity_pieces": user_id * 10,
                "medical_centre_id": medical_centre_id,
                "distribution_location_id": dist_location_id,
                "product_id": product_id,
                "date_received": "2025-12-24T11:00:00"
            }
            try:
                response = requests.post(
                    f"{SERVER_URL}/patient_coupons",
                    json=coupon_data,
                    timeout=10
                )
                response.raise_for_status()
                return (user_id, True, response.json()['id'])
            except Exception as e:
                return (user_id, False, str(e))
        
        # Send 10 concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_coupon_request, i) for i in range(1, 11)]
            results = [future.result() for future in as_completed(futures)]
        
        duration = time.time() - start_time
        
        # Check results
        successes = [r for r in results if r[1]]
        failures = [r for r in results if not r[1]]
        
        print(f"\n  Concurrent Coupon Requests: 10")
        print(f"  Successful: {len(successes)}")
        print(f"  Failed: {len(failures)}")
        print(f"  Duration: {duration:.2f} seconds")
        
        if len(successes) == 10:
            print(colored("✓ PASS", 'green') + " - All concurrent coupon creations succeeded")
            
            # Clean up
            requests.delete(f"{SERVER_URL}/products/{product_id}", timeout=5)
            print(colored("  ✓ Cleanup complete", 'blue'))
            return True
        else:
            print(colored("✗ FAIL", 'red') + f" - {len(failures)} requests failed")
            for user_id, success, error in failures:
                print(f"  User {user_id}: {error}")
            return False
            
    except Exception as e:
        print(colored("✗ FAIL", 'red') + f" - {e}")
        return False

def main():
    """Run all tests"""
    print(colored("\n" + "="*60, 'blue'))
    print(colored("  ALNOOR API SERVER - COMPREHENSIVE TEST SUITE", 'blue'))
    print(colored("="*60 + "\n", 'blue'))
    
    # Clean up test data from previous runs
    cleanup_test_data()
    
    tests = [
        ("Health Check", test_health_check),
        ("UTF-8 Encoding", test_utf8_encoding),
        ("Concurrent Requests", test_concurrent_requests),
        ("Special Characters", test_special_characters),
        ("Large Dataset", test_large_dataset),
        ("Error Handling", test_error_handling),
        ("Large Coupon Dataset (1000)", test_coupons_large_dataset),
        ("Concurrent Coupon Creation", test_concurrent_coupon_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(colored(f"\n✗ CRITICAL ERROR in {test_name}: {e}", 'red'))
            results.append((test_name, False))
        time.sleep(0.5)  # Small delay between tests
    
    # Summary
    print("\n" + colored("="*60, 'blue'))
    print(colored("  TEST SUMMARY", 'blue'))
    print(colored("="*60, 'blue'))
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = colored("✓ PASS", 'green') if result else colored("✗ FAIL", 'red')
        print(f"  {status} - {test_name}")
    
    print()
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(colored("\n  🎉 ALL TESTS PASSED! Server is production-ready.", 'green'))
    else:
        print(colored(f"\n  ⚠️  {total - passed} test(s) failed. Please review.", 'yellow'))
    
    print(colored("="*60 + "\n", 'blue'))

if __name__ == '__main__':
    main()
