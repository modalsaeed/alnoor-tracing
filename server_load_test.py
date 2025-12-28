"""
server_load_test.py - Script to test server capabilities by bulk adding products, pharmacies, distribution locations, purchase orders, supplier purchases, transactions, and coupons.

Usage: python server_load_test.py
"""
import random
from datetime import datetime, timedelta
from src.database.db_client import DatabaseClient
from src.database.models import Product, Pharmacy, DistributionLocation, PurchaseOrder, Purchase, Transaction, PatientCoupon

# CONFIGURATION
SERVER_URL = "http://192.168.100.155:5000"  # Update if needed

def random_date(start, end):
    """Return a random datetime between start and end."""
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def main():
    db = DatabaseClient(SERVER_URL)
    print("[1] Adding product...")
    product = db.create_product(
        name="Test Product",
        reference=f"TP-{random.randint(1000,9999)}",
        unit="pcs",
        description="Load test product"
    )
    print("  Product ID:", product['id'])


    print("[2] Adding health centre...")
    health_centre = db.create_medical_centre(
        name="Test Health Centre",
        reference=f"HC-{random.randint(1000,9999)}",
        address="456 Health Ave"
    )
    print("  Health Centre ID:", health_centre['id'])

    print("[3] Adding pharmacy...")
    pharmacy = db.create_pharmacy(
        name="Test Pharmacy",
        reference=f"PH-{random.randint(1000,9999)}",
        contact_person="Pharmacy Contact",
        phone="12345678",
        notes="123 Test St"
    )
    print("  Pharmacy ID:", pharmacy['id'])

    print("[4] Adding 3 distribution locations...")
    dist_locations = []
    for i in range(3):
        loc = db.create_distribution_location(
            name=f"Dist Location {i+1}",
            reference=f"DL-{random.randint(1000,9999)}",
            pharmacy_id=pharmacy['id'],
            address=f"{i+1} Test Ave"
        )
        dist_locations.append(loc)
        print(f"  Location {i+1} ID:", loc['id'])

    print("[5] Adding purchase order...")
    po = db.create_purchase_order(
        product_id=product['id'],
        quantity=2000,
        po_reference=f"PO-{random.randint(1000,9999)}",
        unit_price=1.5,
        remaining_stock=2000
    )
    print("  PO ID:", po['id'])

    print("[6] Adding supplier purchase linked to PO...")
    purchase = db.create_purchase(
        invoice_number=f"INV-{random.randint(1000,9999)}",
        purchase_order_id=po['id'],
        product_id=product['id'],
        quantity=2000,
        unit_price=1.5,
        total_price=2000*1.5,
        remaining_stock=2000,
        supplier_name="Test Supplier"
    )
    print("  Purchase ID:", purchase['id'])

    print("[7] Adding transactions for each dist location...")
    txn_qty = 300  # Each location gets 300, so 900 total, leaving 1100 in stock
    transactions = []
    for loc in dist_locations:
        txn = db.create_transaction(
            purchase_id=purchase['id'],
            product_id=product['id'],
            quantity=txn_qty,
            distribution_location_id=loc['id'],
            transaction_date=datetime.now().isoformat()
        )
        transactions.append(txn)
        print(f"  Transaction for location {loc['id']} ID:", txn['id'])


    print("[8] Adding 200 coupons for each dist location (total 600)...")
    today = datetime.now()
    last_month = today - timedelta(days=30)
    for idx, loc in enumerate(dist_locations):
        coupons_data = []
        for i in range(200):
            qty = random.choice([160, 320])
            date_received = random_date(last_month, today)
            coupons_data.append({
                "coupon_reference": f"CPN-{idx+1}-{i+1:03d}",
                "product_id": product['id'],
                "quantity_pieces": qty,
                "medical_centre_id": health_centre['id'],
                "distribution_location_id": loc['id'],
                "date_received": date_received.isoformat(),
                "patient_name": f"Patient {idx+1}-{i+1}",
                "cpr": f"{random.randint(100000000,999999999)}",
                "verified": False
            })
        print(f"  Bulk adding 200 coupons for location {loc['id']}...")
        result = db.create_patient_coupons_batch(coupons_data)
        print(f"    Added {len(result)} coupons.")

    print("[DONE] Server load test completed.")

if __name__ == "__main__":
    main()
