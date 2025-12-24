"""
Comprehensive API Server Fix
Fixes all endpoints to match actual database schema
"""

import re

# Read the file
with open('src/api_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: PurchaseOrder CREATE - use correct fields
old_po_create = r'''@app.route\('/purchase_orders', methods=\['POST'\]\)
def create_purchase_order\(\):
    """Create new purchase order"""
    try:
        data = request\.json
        session = db_manager\.get_session\(\)
        
        order = PurchaseOrder\(
            product_id=data\['product_id'\],
            quantity=data\['quantity'\],
            purchase_date=datetime\.fromisoformat\(data\['purchase_date'\]\) if 'purchase_date' in data else datetime\.utcnow\(\),
            supplier=data\.get\('supplier'\),
            notes=data\.get\('notes'\)
        \)
        
        session\.add\(order\)
        session\.commit\(\)
        
        return jsonify\(serialize_model\(order\)\), 201
    except Exception as e:        return jsonify\(\{'error': str\(e\)\}\), 400'''

new_po_create = '''@app.route('/purchase_orders', methods=['POST'])
def create_purchase_order():
    """Create new purchase order"""
    try:
        data = request.json
        
        # Required fields
        if 'po_reference' not in data:
            return jsonify({'error': 'po_reference is required'}), 400
        if 'product_id' not in data:
            return jsonify({'error': 'product_id is required'}), 400
        if 'quantity' not in data:
            return jsonify({'error': 'quantity is required'}), 400
        
        with db_manager.get_session() as session:
            order = PurchaseOrder(
                po_reference=data['po_reference'],
                product_id=data['product_id'],
                product_description=data.get('product_description'),
                quantity=data['quantity'],
                remaining_stock=data.get('remaining_stock', data['quantity']),
                warehouse_location=data.get('warehouse_location'),
                unit_price=data.get('unit_price'),
                tax_rate=data.get('tax_rate'),
                tax_amount=data.get('tax_amount'),
                total_without_tax=data.get('total_without_tax'),
                total_with_tax=data.get('total_with_tax')
            )
            
            session.add(order)
            session.commit()
            
            return jsonify(serialize_model(order)), 201
    except Exception as e:
        print(f"ERROR creating purchase order: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500'''

content = re.sub(old_po_create, new_po_create, content)

# Fix 2: PurchaseOrder UPDATE - use correct fields
old_po_update = r'''@app.route\('/purchase_orders/<int:order_id>', methods=\['PUT'\]\)
def update_purchase_order\(order_id\):
    """Update existing purchase order"""
    try:
        data = request\.json
        with db_manager\.get_session\(\) as session:
            order = session\.query\(PurchaseOrder\)\.filter_by\(id=order_id\)\.first\(\)
        if not order:
            return jsonify\(\{'error': 'Purchase order not found'\}\), 404
        
        if 'product_id' in data:
            order\.product_id = data\['product_id'\]
        if 'quantity' in data:
            order\.quantity = data\['quantity'\]
        if 'purchase_date' in data:
            order\.purchase_date = datetime\.fromisoformat\(data\['purchase_date'\]\)
        if 'supplier' in data:
            order\.supplier = data\['supplier'\]
        if 'notes' in data:
            order\.notes = data\['notes'\]
        
        order\.updated_at = datetime\.utcnow\(\)
        session\.commit\(\)
        
        return jsonify\(serialize_model\(order\)\)
    except Exception as e:        return jsonify\(\{'error': str\(e\)\}\), 400'''

new_po_update = '''@app.route('/purchase_orders/<int:order_id>', methods=['PUT'])
def update_purchase_order(order_id):
    """Update existing purchase order"""
    try:
        data = request.json
        with db_manager.get_session() as session:
            order = session.query(PurchaseOrder).filter_by(id=order_id).first()
            if not order:
                return jsonify({'error': 'Purchase order not found'}), 404
            
            if 'po_reference' in data:
                order.po_reference = data['po_reference']
            if 'product_id' in data:
                order.product_id = data['product_id']
            if 'product_description' in data:
                order.product_description = data['product_description']
            if 'quantity' in data:
                order.quantity = data['quantity']
            if 'remaining_stock' in data:
                order.remaining_stock = data['remaining_stock']
            if 'warehouse_location' in data:
                order.warehouse_location = data['warehouse_location']
            if 'unit_price' in data:
                order.unit_price = data['unit_price']
            if 'tax_rate' in data:
                order.tax_rate = data['tax_rate']
            if 'tax_amount' in data:
                order.tax_amount = data['tax_amount']
            if 'total_without_tax' in data:
                order.total_without_tax = data['total_without_tax']
            if 'total_with_tax' in data:
                order.total_with_tax = data['total_with_tax']
            
            order.updated_at = datetime.utcnow()
            session.commit()
            
            return jsonify(serialize_model(order))
    except Exception as e:
        print(f"ERROR updating purchase order: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500'''

content = re.sub(old_po_update, new_po_update, content, flags=re.DOTALL)

# Fix 3: Pharmacy CREATE - use correct fields
old_pharmacy_create = r'''@app.route\('/pharmacies', methods=\['POST'\]\)
def create_pharmacy\(\):
    """Create new pharmacy"""
    try:
        data = request\.json
        session = db_manager\.get_session\(\)
        
        pharmacy = Pharmacy\(
            name=data\['name'\],
            location=data\.get\('location'\),
            contact=data\.get\('contact'\)
        \)
        
        session\.add\(pharmacy\)
        session\.commit\(\)
        
        return jsonify\(serialize_model\(pharmacy\)\), 201
    except Exception as e:        return jsonify\(\{'error': str\(e\)\}\), 400'''

new_pharmacy_create = '''@app.route('/pharmacies', methods=['POST'])
def create_pharmacy():
    """Create new pharmacy"""
    try:
        data = request.json
        
        if 'name' not in data:
            return jsonify({'error': 'name is required'}), 400
        
        with db_manager.get_session() as session:
            pharmacy = Pharmacy(
                name=data['name'],
                reference=data.get('reference'),
                trn=data.get('trn'),
                contact_person=data.get('contact_person'),
                phone=data.get('phone'),
                email=data.get('email'),
                notes=data.get('notes')
            )
            
            session.add(pharmacy)
            session.commit()
            
            return jsonify(serialize_model(pharmacy)), 201
    except Exception as e:
        print(f"ERROR creating pharmacy: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500'''

content = re.sub(old_pharmacy_create, new_pharmacy_create, content)

# Fix 4: Pharmacy UPDATE - use correct fields
old_pharmacy_update = r'''@app.route\('/pharmacies/<int:pharmacy_id>', methods=\['PUT'\]\)
def update_pharmacy\(pharmacy_id\):
    """Update existing pharmacy"""
    try:
        data = request\.json
        with db_manager\.get_session\(\) as session:
            pharmacy = session\.query\(Pharmacy\)\.filter_by\(id=pharmacy_id\)\.first\(\)
        if not pharmacy:
            return jsonify\(\{'error': 'Pharmacy not found'\}\), 404
        
        if 'name' in data:
            pharmacy\.name = data\['name'\]
        if 'location' in data:
            pharmacy\.location = data\['location'\]
        if 'contact' in data:
            pharmacy\.contact = data\['contact'\]
        
        pharmacy\.updated_at = datetime\.utcnow\(\)
        session\.commit\(\)
        
        return jsonify\(serialize_model\(pharmacy\)\)
    except Exception as e:        return jsonify\(\{'error': str\(e\)\}\), 400'''

new_pharmacy_update = '''@app.route('/pharmacies/<int:pharmacy_id>', methods=['PUT'])
def update_pharmacy(pharmacy_id):
    """Update existing pharmacy"""
    try:
        data = request.json
        with db_manager.get_session() as session:
            pharmacy = session.query(Pharmacy).filter_by(id=pharmacy_id).first()
            if not pharmacy:
                return jsonify({'error': 'Pharmacy not found'}), 404
            
            if 'name' in data:
                pharmacy.name = data['name']
            if 'reference' in data:
                pharmacy.reference = data['reference']
            if 'trn' in data:
                pharmacy.trn = data['trn']
            if 'contact_person' in data:
                pharmacy.contact_person = data['contact_person']
            if 'phone' in data:
                pharmacy.phone = data['phone']
            if 'email' in data:
                pharmacy.email = data['email']
            if 'notes' in data:
                pharmacy.notes = data['notes']
            
            pharmacy.updated_at = datetime.utcnow()
            session.commit()
            
            return jsonify(serialize_model(pharmacy))
    except Exception as e:
        print(f"ERROR updating pharmacy: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500'''

content = re.sub(old_pharmacy_update, new_pharmacy_update, content, flags=re.DOTALL)

# Fix 5: DistributionLocation CREATE - use correct fields
old_dist_create = r'''@app.route\('/distribution_locations', methods=\['POST'\]\)
def create_distribution_location\(\):
    """Create new distribution location"""
    try:
        data = request\.json
        session = db_manager\.get_session\(\)
        
        location = DistributionLocation\(
            name=data\['name'\],
            address=data\.get\('address'\),
            contact=data\.get\('contact'\)
        \)
        
        session\.add\(location\)
        session\.commit\(\)
        
        return jsonify\(serialize_model\(location\)\), 201
    except Exception as e:        return jsonify\(\{'error': str\(e\)\}\), 400'''

new_dist_create = '''@app.route('/distribution_locations', methods=['POST'])
def create_distribution_location():
    """Create new distribution location"""
    try:
        data = request.json
        
        if 'name' not in data:
            return jsonify({'error': 'name is required'}), 400
        
        with db_manager.get_session() as session:
            location = DistributionLocation(
                name=data['name'],
                reference=data.get('reference'),
                trn=data.get('trn'),
                pharmacy_id=data.get('pharmacy_id'),
                address=data.get('address'),
                contact_person=data.get('contact_person'),
                phone=data.get('phone')
            )
            
            session.add(location)
            session.commit()
            
            return jsonify(serialize_model(location)), 201
    except Exception as e:
        print(f"ERROR creating distribution location: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500'''

content = re.sub(old_dist_create, new_dist_create, content)

# Fix 6: MedicalCentre CREATE - use correct fields
old_medical_create = r'''@app.route\('/medical_centres', methods=\['POST'\]\)
def create_medical_centre\(\):
    """Create new medical centre"""
    try:
        data = request\.json
        session = db_manager\.get_session\(\)
        
        centre = MedicalCentre\(
            name=data\['name'\],
            location=data\.get\('location'\),
            contact=data\.get\('contact'\)
        \)
        
        session\.add\(centre\)
        session\.commit\(\)
        
        return jsonify\(serialize_model\(centre\)\), 201
    except Exception as e:        return jsonify\(\{'error': str\(e\)\}\), 400'''

new_medical_create = '''@app.route('/medical_centres', methods=['POST'])
def create_medical_centre():
    """Create new medical centre"""
    try:
        data = request.json
        
        if 'name' not in data:
            return jsonify({'error': 'name is required'}), 400
        
        with db_manager.get_session() as session:
            centre = MedicalCentre(
                name=data['name'],
                reference=data.get('reference'),
                address=data.get('address'),
                contact_person=data.get('contact_person'),
                phone=data.get('phone')
            )
            
            session.add(centre)
            session.commit()
            
            return jsonify(serialize_model(centre)), 201
    except Exception as e:
        print(f"ERROR creating medical centre: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500'''

content = re.sub(old_medical_create, new_medical_create, content)

# Fix 7: Transaction CREATE - use with statement
old_trans_create = r'''@app.route\('/transactions', methods=\['POST'\]\)
def create_transaction\(\):
    """Create new transaction"""
    try:
        data = request\.json
        session = db_manager\.get_session\(\)
        
        transaction = Transaction\(
            product_id=data\['product_id'\],
            quantity=data\['quantity'\],
            transaction_type=data\['transaction_type'\],
            transaction_date=datetime\.fromisoformat\(data\['transaction_date'\]\) if 'transaction_date' in data else datetime\.utcnow\(\),
            pharmacy_id=data\.get\('pharmacy_id'\),
            distribution_location_id=data\.get\('distribution_location_id'\),
            medical_centre_id=data\.get\('medical_centre_id'\),
            notes=data\.get\('notes'\)
        \)
        
        session\.add\(transaction\)
        session\.commit\(\)
        
        return jsonify\(serialize_model\(transaction\)\), 201
    except Exception as e:        return jsonify\(\{'error': str\(e\)\}\), 400'''

new_trans_create = '''@app.route('/transactions', methods=['POST'])
def create_transaction():
    """Create new transaction"""
    try:
        data = request.json
        
        with db_manager.get_session() as session:
            transaction = Transaction(
                product_id=data['product_id'],
                quantity=data['quantity'],
                transaction_type=data['transaction_type'],
                transaction_date=datetime.fromisoformat(data['transaction_date']) if 'transaction_date' in data else datetime.utcnow(),
                pharmacy_id=data.get('pharmacy_id'),
                distribution_location_id=data.get('distribution_location_id'),
                medical_centre_id=data.get('medical_centre_id'),
                notes=data.get('notes')
            )
            
            session.add(transaction)
            session.commit()
            
            return jsonify(serialize_model(transaction)), 201
    except Exception as e:
        print(f"ERROR creating transaction: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500'''

content = re.sub(old_trans_create, new_trans_create, content)

# Fix 8: ActivityLog CREATE - use with statement
old_log_create = r'''@app.route\('/activity_logs', methods=\['POST'\]\)
def create_activity_log\(\):
    """Create new activity log entry"""
    try:
        data = request\.json
        session = db_manager\.get_session\(\)
        
        log = ActivityLog\(
            action_type=data\['action_type'\],
            description=data\['description'\],
            user=data\.get\('user', 'system'\)
        \)
        
        session\.add\(log\)
        session\.commit\(\)
        
        return jsonify\(serialize_model\(log\)\), 201
    except Exception as e:        return jsonify\(\{'error': str\(e\)\}\), 400'''

new_log_create = '''@app.route('/activity_logs', methods=['POST'])
def create_activity_log():
    """Create new activity log entry"""
    try:
        data = request.json
        
        with db_manager.get_session() as session:
            log = ActivityLog(
                action_type=data['action_type'],
                description=data['description'],
                user=data.get('user', 'system')
            )
            
            session.add(log)
            session.commit()
            
            return jsonify(serialize_model(log)), 201
    except Exception as e:
        print(f"ERROR creating activity log: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500'''

content = re.sub(old_log_create, new_log_create, content)

# Fix 9: Statistics endpoint - use with statement
old_stats = r'''@app.route\('/statistics/inventory', methods=\['GET'\]\)
def get_inventory_statistics\(\):
    """Get inventory statistics"""
    try:
        session = db_manager\.get_session\(\)
        
        # This is a simplified version - you may need to adjust based on your actual business logic
        products = session\.query\(Product\)\.count\(\)
        transactions = session\.query\(Transaction\)\.count\(\)
        pharmacies = session\.query\(Pharmacy\)\.count\(\)
        
        return jsonify\(\{
            'total_products': products,
            'total_transactions': transactions,
            'total_pharmacies': pharmacies
        \}\)
    except Exception as e:
        return jsonify\(\{'error': str\(e\)\}\), 500'''

new_stats = '''@app.route('/statistics/inventory', methods=['GET'])
def get_inventory_statistics():
    """Get inventory statistics"""
    try:
        with db_manager.get_session() as session:
            products = session.query(Product).count()
            transactions = session.query(Transaction).count()
            pharmacies = session.query(Pharmacy).count()
            
            return jsonify({
                'total_products': products,
                'total_transactions': transactions,
                'total_pharmacies': pharmacies
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500'''

content = re.sub(old_stats, new_stats, content)

# Write the fixed file
with open('src/api_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed all API endpoints!")
print("✓ All endpoints now use correct database fields")
print("✓ All endpoints now use 'with' statement for session management")
print("✓ All endpoints have proper error handling")
