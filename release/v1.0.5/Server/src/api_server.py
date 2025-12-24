"""
Alnoor Medical Services - REST API Server

This server provides HTTP API access to the SQLite database,
enabling multiple users to work concurrently without data conflicts.

Server Mode: Run this script on the PC that hosts the database
Client Mode: Apps connect to this server via HTTP instead of direct SQLite access
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_manager import DatabaseManager
from src.database.models import (
    Product, PurchaseOrder, Purchase, Pharmacy,
    DistributionLocation, MedicalCentre, PatientCoupon,
    Transaction, ActivityLog
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database manager
db_manager = None


def init_db():
    """Initialize database connection"""
    global db_manager
    db_manager = DatabaseManager()
    print("✅ Database initialized successfully")


def serialize_model(obj):
    """Convert SQLAlchemy model to dictionary"""
    if obj is None:
        return None
    
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        # Convert datetime to ISO format string
        if isinstance(value, datetime):
            value = value.isoformat()
        result[column.name] = value
    return result


def serialize_list(objects):
    """Convert list of SQLAlchemy models to list of dictionaries"""
    return [serialize_model(obj) for obj in objects]


# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Check if server is running"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.4'
    })


# ==================== PRODUCT ENDPOINTS ====================

@app.route('/products', methods=['GET'])
def get_products():
    """Get all products"""
    try:
        session = db_manager.get_session()
        products = session.query(Product).all()
        return jsonify(serialize_list(products))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get product by ID"""
    try:
        session = db_manager.get_session()
        product = session.query(Product).filter_by(id=product_id).first()
        if product:
            return jsonify(serialize_model(product))
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/products', methods=['POST'])
def create_product():
    """Create new product"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        product = Product(
            name=data['name'],
            reference=data['reference'],
            unit=data.get('unit'),
            description=data.get('description')
        )
        
        session.add(product)
        session.commit()
        
        return jsonify(serialize_model(product)), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update existing product"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if 'name' in data:
            product.name = data['name']
        if 'reference' in data:
            product.reference = data['reference']
        if 'unit' in data:
            product.unit = data['unit']
        if 'description' in data:
            product.description = data['description']
        
        product.updated_at = datetime.utcnow()
        session.commit()
        
        return jsonify(serialize_model(product))
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete product"""
    try:
        session = db_manager.get_session()
        
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        session.delete(product)
        session.commit()
        
        return jsonify({'message': 'Product deleted successfully'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


# ==================== PURCHASE ORDER ENDPOINTS ====================

@app.route('/purchase_orders', methods=['GET'])
def get_purchase_orders():
    """Get all purchase orders"""
    try:
        session = db_manager.get_session()
        orders = session.query(PurchaseOrder).all()
        return jsonify(serialize_list(orders))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/purchase_orders/<int:order_id>', methods=['GET'])
def get_purchase_order(order_id):
    """Get purchase order by ID"""
    try:
        session = db_manager.get_session()
        order = session.query(PurchaseOrder).filter_by(id=order_id).first()
        if order:
            return jsonify(serialize_model(order))
        return jsonify({'error': 'Purchase order not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/purchase_orders', methods=['POST'])
def create_purchase_order():
    """Create new purchase order"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        order = PurchaseOrder(
            product_id=data['product_id'],
            quantity=data['quantity'],
            purchase_date=datetime.fromisoformat(data['purchase_date']) if 'purchase_date' in data else datetime.utcnow(),
            supplier=data.get('supplier'),
            notes=data.get('notes')
        )
        
        session.add(order)
        session.commit()
        
        return jsonify(serialize_model(order)), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/purchase_orders/<int:order_id>', methods=['PUT'])
def update_purchase_order(order_id):
    """Update existing purchase order"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        order = session.query(PurchaseOrder).filter_by(id=order_id).first()
        if not order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        if 'product_id' in data:
            order.product_id = data['product_id']
        if 'quantity' in data:
            order.quantity = data['quantity']
        if 'purchase_date' in data:
            order.purchase_date = datetime.fromisoformat(data['purchase_date'])
        if 'supplier' in data:
            order.supplier = data['supplier']
        if 'notes' in data:
            order.notes = data['notes']
        
        order.updated_at = datetime.utcnow()
        session.commit()
        
        return jsonify(serialize_model(order))
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/purchase_orders/<int:order_id>', methods=['DELETE'])
def delete_purchase_order(order_id):
    """Delete purchase order"""
    try:
        session = db_manager.get_session()
        
        order = session.query(PurchaseOrder).filter_by(id=order_id).first()
        if not order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        session.delete(order)
        session.commit()
        
        return jsonify({'message': 'Purchase order deleted successfully'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


# ==================== PHARMACY ENDPOINTS ====================

@app.route('/pharmacies', methods=['GET'])
def get_pharmacies():
    """Get all pharmacies"""
    try:
        session = db_manager.get_session()
        pharmacies = session.query(Pharmacy).all()
        return jsonify(serialize_list(pharmacies))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/pharmacies', methods=['POST'])
def create_pharmacy():
    """Create new pharmacy"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        pharmacy = Pharmacy(
            name=data['name'],
            location=data.get('location'),
            contact=data.get('contact')
        )
        
        session.add(pharmacy)
        session.commit()
        
        return jsonify(serialize_model(pharmacy)), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/pharmacies/<int:pharmacy_id>', methods=['PUT'])
def update_pharmacy(pharmacy_id):
    """Update existing pharmacy"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        pharmacy = session.query(Pharmacy).filter_by(id=pharmacy_id).first()
        if not pharmacy:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        if 'name' in data:
            pharmacy.name = data['name']
        if 'location' in data:
            pharmacy.location = data['location']
        if 'contact' in data:
            pharmacy.contact = data['contact']
        
        pharmacy.updated_at = datetime.utcnow()
        session.commit()
        
        return jsonify(serialize_model(pharmacy))
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/pharmacies/<int:pharmacy_id>', methods=['DELETE'])
def delete_pharmacy(pharmacy_id):
    """Delete pharmacy"""
    try:
        session = db_manager.get_session()
        
        pharmacy = session.query(Pharmacy).filter_by(id=pharmacy_id).first()
        if not pharmacy:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        session.delete(pharmacy)
        session.commit()
        
        return jsonify({'message': 'Pharmacy deleted successfully'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


# ==================== TRANSACTION ENDPOINTS ====================

@app.route('/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions with optional filtering"""
    try:
        session = db_manager.get_session()
        query = session.query(Transaction)
        
        # Optional filters
        product_id = request.args.get('product_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if product_id:
            query = query.filter(Transaction.product_id == product_id)
        if start_date:
            query = query.filter(Transaction.transaction_date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Transaction.transaction_date <= datetime.fromisoformat(end_date))
        
        transactions = query.all()
        return jsonify(serialize_list(transactions))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/transactions', methods=['POST'])
def create_transaction():
    """Create new transaction"""
    try:
        data = request.json
        session = db_manager.get_session()
        
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
        session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Delete transaction"""
    try:
        session = db_manager.get_session()
        
        transaction = session.query(Transaction).filter_by(id=transaction_id).first()
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        session.delete(transaction)
        session.commit()
        
        return jsonify({'message': 'Transaction deleted successfully'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


# ==================== ACTIVITY LOG ENDPOINTS ====================

@app.route('/activity_logs', methods=['GET'])
def get_activity_logs():
    """Get activity logs with optional filtering"""
    try:
        session = db_manager.get_session()
        query = session.query(ActivityLog)
        
        # Optional filters
        limit = request.args.get('limit', type=int, default=100)
        action_type = request.args.get('action_type')
        
        if action_type:
            query = query.filter(ActivityLog.action_type == action_type)
        
        logs = query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
        return jsonify(serialize_list(logs))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/activity_logs', methods=['POST'])
def create_activity_log():
    """Create new activity log entry"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        log = ActivityLog(
            action_type=data['action_type'],
            description=data['description'],
            user=data.get('user', 'system')
        )
        
        session.add(log)
        session.commit()
        
        return jsonify(serialize_model(log)), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


# ==================== DISTRIBUTION LOCATION ENDPOINTS ====================

@app.route('/distribution_locations', methods=['GET'])
def get_distribution_locations():
    """Get all distribution locations"""
    try:
        session = db_manager.get_session()
        locations = session.query(DistributionLocation).all()
        return jsonify(serialize_list(locations))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/distribution_locations', methods=['POST'])
def create_distribution_location():
    """Create new distribution location"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        location = DistributionLocation(
            name=data['name'],
            address=data.get('address'),
            contact=data.get('contact')
        )
        
        session.add(location)
        session.commit()
        
        return jsonify(serialize_model(location)), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


# ==================== MEDICAL CENTRE ENDPOINTS ====================

@app.route('/medical_centres', methods=['GET'])
def get_medical_centres():
    """Get all medical centres"""
    try:
        session = db_manager.get_session()
        centres = session.query(MedicalCentre).all()
        return jsonify(serialize_list(centres))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/medical_centres', methods=['POST'])
def create_medical_centre():
    """Create new medical centre"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        centre = MedicalCentre(
            name=data['name'],
            location=data.get('location'),
            contact=data.get('contact')
        )
        
        session.add(centre)
        session.commit()
        
        return jsonify(serialize_model(centre)), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


# ==================== PATIENT COUPON ENDPOINTS ====================

@app.route('/patient_coupons', methods=['GET'])
def get_patient_coupons():
    """Get all patient coupons"""
    try:
        session = db_manager.get_session()
        coupons = session.query(PatientCoupon).all()
        return jsonify(serialize_list(coupons))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/patient_coupons', methods=['POST'])
def create_patient_coupon():
    """Create new patient coupon"""
    try:
        data = request.json
        session = db_manager.get_session()
        
        coupon = PatientCoupon(
            coupon_number=data['coupon_number'],
            patient_name=data.get('patient_name'),
            issue_date=datetime.fromisoformat(data['issue_date']) if 'issue_date' in data else datetime.utcnow(),
            expiry_date=datetime.fromisoformat(data['expiry_date']) if 'expiry_date' in data else None,
            is_used=data.get('is_used', False)
        )
        
        session.add(coupon)
        session.commit()
        
        return jsonify(serialize_model(coupon)), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400


# ==================== STATISTICS ENDPOINTS ====================

@app.route('/statistics/inventory', methods=['GET'])
def get_inventory_statistics():
    """Get inventory statistics"""
    try:
        session = db_manager.get_session()
        
        # This is a simplified version - you may need to adjust based on your actual business logic
        products = session.query(Product).count()
        transactions = session.query(Transaction).count()
        pharmacies = session.query(Pharmacy).count()
        
        return jsonify({
            'total_products': products,
            'total_transactions': transactions,
            'total_pharmacies': pharmacies
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SERVER STARTUP ====================

def main():
    """Start the API server"""
    print("=" * 60)
    print("Alnoor Medical Services - API Server")
    print("=" * 60)
    print()
    
    # Initialize database
    init_db()
    
    # Get server configuration
    host = os.environ.get('ALNOOR_API_HOST', '0.0.0.0')
    port = int(os.environ.get('ALNOOR_API_PORT', 5000))
    
    print(f"🚀 Starting server on http://{host}:{port}")
    print(f"📊 Health check: http://{host}:{port}/health")
    print()
    print("To stop the server, press Ctrl+C")
    print("=" * 60)
    print()
    
    # Start Flask server
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
