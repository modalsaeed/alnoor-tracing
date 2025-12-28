import shutil
import threading
import time

"""
Alnoor Medical Services - REST API Server

This server provides HTTP API access to the SQLite database,
enabling multiple users to work concurrently without data conflicts.

Server Mode: Run this script on the PC that hosts the database
Client Mode: Apps connect to this server via HTTP instead of direct SQLite access
"""

import os
import sys
import traceback
import logging
import shutil
import threading
import time
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

# ==================== BACKUP CONFIG ====================
BACKUP_DIR = Path(__file__).parent.parent / 'backups'
MANUAL_BACKUP_DIR = BACKUP_DIR / 'manual'
WEEKLY_BACKUP_DIR = BACKUP_DIR / 'weekly'
BACKUP_DIR.mkdir(exist_ok=True)
MANUAL_BACKUP_DIR.mkdir(exist_ok=True)
WEEKLY_BACKUP_DIR.mkdir(exist_ok=True)

# Retention policies
WEEKLY_RETENTION = 12  # weeks
MANUAL_RETENTION_DAYS = 30

def get_db_path():
    if db_manager:
        return Path(db_manager.db_path)
    return None

def make_backup(backup_type='manual'):
    """Create a backup of the database file."""
    db_path = get_db_path()
    if not db_path or not db_path.exists():
        raise RuntimeError("Database file not found for backup.")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if backup_type == 'manual':
        dest_dir = MANUAL_BACKUP_DIR
        fname = f'manual_{timestamp}.sqlite'
    elif backup_type == 'weekly':
        dest_dir = WEEKLY_BACKUP_DIR
        fname = f'weekly_{timestamp}.sqlite'
    else:
        raise ValueError(f"Unknown backup type: {backup_type}")

    dest_dir.mkdir(exist_ok=True)
    backup_path = dest_dir / fname
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
    except Exception as e:
        raise RuntimeError(f"Backup failed: {e}")
    return backup_path

def schedule_weekly_backup():
    """Run weekly backup in a background thread."""
    def run():
        while True:
            now = datetime.now()
            # Run every Monday at 2am
            next_run = (now + timedelta(days=(7-now.weekday())%7)).replace(hour=2, minute=0, second=0, microsecond=0)
            sleep_time = (next_run - now).total_seconds()
            time.sleep(max(sleep_time, 0))
            make_backup('weekly')
            cleanup_backups()
    t = threading.Thread(target=run, daemon=True)
    t.start()

def cleanup_backups():
    """Remove old manual and weekly backups according to retention policy."""
    # Cleanup manual backups older than MANUAL_RETENTION_DAYS
    cutoff_manual = time.time() - MANUAL_RETENTION_DAYS * 86400
    for f in MANUAL_BACKUP_DIR.glob('manual_*.sqlite'):
        try:
            if f.stat().st_mtime < cutoff_manual:
                f.unlink()
        except Exception as e:
            app.logger.warning(f"Failed to delete old manual backup {f}: {e}")

    # Cleanup weekly backups, keep only the most recent WEEKLY_RETENTION
    weekly_files = sorted(WEEKLY_BACKUP_DIR.glob('weekly_*.sqlite'), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in weekly_files[WEEKLY_RETENTION:]:
        try:
            f.unlink()
        except Exception as e:
            app.logger.warning(f"Failed to delete old weekly backup {f}: {e}")
            
schedule_weekly_backup()

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
import traceback
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_manager import DatabaseManager
from src.database.models import (
    Product, PurchaseOrder, Purchase, Pharmacy,
    DistributionLocation, MedicalCentre, PatientCoupon,
    Transaction, ActivityLog, DeliveryNote
)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Allow Unicode characters in JSON
CORS(app)  # Enable CORS for all routes

# Initialize database manager
db_manager = None

# Logging flag (can be enabled via environment variable)
ENABLE_LOGGING = os.environ.get('ALNOOR_ENABLE_LOGGING', 'false').lower() == 'true'

# Track active connections
active_clients = set()

@app.before_request
def log_request_info():
    """Log incoming request details"""
    if ENABLE_LOGGING:
        client_ip = request.remote_addr
        # Track new client connections
        if client_ip not in active_clients:
            active_clients.add(client_ip)
            app.logger.info(f"🔌 NEW CLIENT CONNECTED: {client_ip}")
            app.logger.info(f"   Total active clients: {len(active_clients)}")
        
        # Log request details
        method = request.method
        path = request.path
        app.logger.info(f"📨 [{client_ip}] {method} {path}")
        
        # Store request start time for duration calculation
        request.start_time = datetime.now()

@app.after_request
def log_response_info(response):
    """Log response details"""
    if ENABLE_LOGGING and hasattr(request, 'start_time'):
        duration = (datetime.now() - request.start_time).total_seconds()
        client_ip = request.remote_addr
        method = request.method
        path = request.path
        status = response.status_code
        
        # Format status with emoji
        if status < 300:
            status_emoji = "✅"
        elif status < 400:
            status_emoji = "➡️"
        elif status < 500:
            status_emoji = "⚠️"
        else:
            status_emoji = "❌"
        
        app.logger.info(f"📤 [{client_ip}] {method} {path} → {status_emoji} {status} ({duration:.3f}s)")
    
    return response

def setup_logging():
    """Configure logging for the API server"""
    if ENABLE_LOGGING:
        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parent.parent / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create log filename with timestamp
        log_filename = logs_dir / f"api_server_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configure logging to both console and file
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(message)s',
            datefmt='%H:%M:%S',
            handlers=[
                logging.StreamHandler(),  # Console output
                logging.FileHandler(log_filename, encoding='utf-8')  # File output
            ]
        )
        app.logger.setLevel(logging.INFO)
        print(f"📝 Logging enabled - saving to: {log_filename.absolute()}")
        app.logger.info("="*70)
        app.logger.info("🚀 API SERVER STARTED")
        app.logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        app.logger.info("="*70)
    else:
        # Disable Flask default logger and Waitress logger
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        waitress_log = logging.getLogger('waitress')
        waitress_log.setLevel(logging.ERROR)

def log_request(endpoint_name, details=""):
    """Log API request if logging is enabled"""
    if ENABLE_LOGGING:
        client_ip = request.remote_addr
        method = request.method
        app.logger.info(f"{client_ip} - {method} {endpoint_name} {details}")

def log_success(message):
    """Log successful operation if logging is enabled"""
    if ENABLE_LOGGING:
        app.logger.info(f"✓ {message}")


def init_db():
    """Initialize database connection"""
    global db_manager
    db_manager = DatabaseManager()
    print("✅ Database initialized successfully")
    print(f"📁 Database location: {db_manager.db_path}")
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

    # --- Add related info for PurchaseOrder, Purchase, Transaction, DeliveryNote ---
    if hasattr(obj, '__tablename__'):
        if obj.__tablename__ == 'purchase_orders':
            # ...existing code...
            product = getattr(obj, 'product', None)
            if product is not None:
                result['product'] = {
                    'id': getattr(product, 'id', None),
                    'name': getattr(product, 'name', None),
                    'reference': getattr(product, 'reference', None),
                }
            else:
                result['product'] = None
                try:
                    app.logger.warning(f"PurchaseOrder id={getattr(obj, 'id', None)} has missing product (product_id={getattr(obj, 'product_id', None)})")
                except Exception:
                    pass
        elif obj.__tablename__ == 'purchases':
            # ...existing code...
            po = getattr(obj, 'purchase_order', None)
            if po is not None:
                result['purchase_order'] = {
                    'id': getattr(po, 'id', None),
                    'po_reference': getattr(po, 'po_reference', None)
                }
            else:
                result['purchase_order'] = None
            product = getattr(obj, 'product', None)
            if product is not None:
                result['product'] = {
                    'id': getattr(product, 'id', None),
                    'name': getattr(product, 'name', None),
                    'reference': getattr(product, 'reference', None)
                }
            else:
                result['product'] = None
        elif obj.__tablename__ == 'transactions':
            # ...existing code...
            purchase = getattr(obj, 'purchase', None)
            if purchase is not None:
                result['purchase'] = {
                    'id': getattr(purchase, 'id', None),
                    'invoice_number': getattr(purchase, 'invoice_number', None)
                }
            else:
                result['purchase'] = None
            product = getattr(obj, 'product', None)
            if product is not None:
                result['product'] = {
                    'id': getattr(product, 'id', None),
                    'name': getattr(product, 'name', None),
                    'reference': getattr(product, 'reference', None)
                }
            else:
                result['product'] = None
            dist_loc = getattr(obj, 'distribution_location', None)
            if dist_loc is not None:
                result['distribution_location'] = {
                    'id': getattr(dist_loc, 'id', None),
                    'name': getattr(dist_loc, 'name', None),
                    'reference': getattr(dist_loc, 'reference', None)
                }
            else:
                result['distribution_location'] = None
        elif obj.__tablename__ == 'delivery_notes':
            # Add related info if needed
            pass
    return result


# ==================== BACKUP ENDPOINTS ====================
@app.route('/backup/manual', methods=['POST'])
def manual_backup():
    """User-initiated backup, returns backup file path."""
    import traceback
    try:
        backup_path = make_backup('manual')
        cleanup_backups()
        if backup_path:
            return jsonify({'success': True, 'backup_path': str(backup_path)}), 201
        else:
            app.logger.error('Backup failed: No backup path returned')
            return jsonify({'error': 'Backup failed: No backup path returned'}), 500
    except Exception as e:
        tb = traceback.format_exc()
        app.logger.error(f"Backup failed: {e}\n{tb}")
        # Return traceback in error for debugging (remove in production)
        return jsonify({'error': str(e), 'traceback': tb}), 500

@app.route('/backup/list', methods=['GET'])
def list_backups():
    """List available backups (weekly and manual)."""
    try:
        weekly = [str(p) for p in sorted(WEEKLY_BACKUP_DIR.glob('weekly_*.sqlite'), key=lambda p: p.stat().st_mtime, reverse=True)]
        manual = [str(p) for p in sorted(MANUAL_BACKUP_DIR.glob('manual_*.sqlite'), key=lambda p: p.stat().st_mtime, reverse=True)]
        return jsonify({'weekly': weekly, 'manual': manual})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ==================== DELIVERY NOTE ENDPOINTS ====================
@app.route('/delivery_notes', methods=['GET'])
def get_delivery_notes():
    """Get all delivery notes"""
    try:
        notes = db_manager.get_all(DeliveryNote)
        return jsonify(serialize_list(notes))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delivery_notes/<int:note_id>', methods=['GET'])
def get_delivery_note(note_id):
    try:
        note = db_manager.get_by_id(DeliveryNote, note_id)
        if note:
            return jsonify(serialize_model(note))
        else:
            return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delivery_notes', methods=['POST'])
def create_delivery_note():
    try:
        data = request.get_json()
        print("[DEBUG] Incoming DeliveryNote data:", data, flush=True)
        import traceback
        try:
            # Convert date_created to datetime if it's a string
            if 'date_created' in data and isinstance(data['date_created'], str):
                from datetime import datetime
                try:
                    data['date_created'] = datetime.fromisoformat(data['date_created'])
                except Exception as dt_err:
                    print(f"[ERROR] Failed to parse date_created: {data['date_created']} - {dt_err}", flush=True)
                    data['date_created'] = datetime.now()
            note = DeliveryNote(**data)
            db_manager.add(note)
            return jsonify(serialize_model(note)), 201
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[ERROR] Failed to create DeliveryNote: {e}\n{tb}", flush=True)
            return jsonify({'error': str(e), 'traceback': tb, 'data': data}), 500
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[ERROR] Unexpected error in create_delivery_note: {e}\n{tb}", flush=True)
        return jsonify({'error': str(e), 'traceback': tb}), 500

@app.route('/delivery_notes/<int:note_id>', methods=['PUT'])
def update_delivery_note(note_id):
    try:
        data = request.get_json()
        note = db_manager.get_by_id(DeliveryNote, note_id)
        if not note:
            return jsonify({'error': 'Not found'}), 404
        for key, value in data.items():
            setattr(note, key, value)
        db_manager.update(note)
        return jsonify(serialize_model(note))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delivery_notes/<int:note_id>', methods=['DELETE'])
def delete_delivery_note(note_id):
    try:
        db_manager.delete(DeliveryNote, note_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def serialize_list(objects):
    """Convert list of SQLAlchemy models to list of dictionaries. Handles None safely."""
    if objects is None:
        return []
    return [serialize_model(obj) for obj in objects]


# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Check if server is running"""
    log_request('/health')
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.10',
        'logging': 'enabled' if ENABLE_LOGGING else 'disabled'
    })


# ==================== PRODUCT ENDPOINTS ====================

@app.route('/products', methods=['GET'])
def get_products():
    """Get all products"""
    import traceback
    try:
        with db_manager.get_session() as session:
            products = session.query(Product).all()
        log_request('/products', f"- Retrieved {len(products)} products")
        return jsonify(serialize_list(products))
    except Exception as e:
        tb = traceback.format_exc()
        print(f"\n[SERVER ERROR] /products\n{tb}\n", flush=True)
        return jsonify({'error': str(e), 'traceback': tb}), 500


@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get product by ID"""
    try:
        with db_manager.get_session() as session:
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
        
        # Required fields
        name = data.get('name')
        reference = data.get('reference')
        
        if not name:
            return jsonify({'error': 'name is required'}), 400
        if not reference:
            return jsonify({'error': 'reference is required'}), 400
        
        with db_manager.get_session() as session:
            product = Product(
                name=name,
                reference=reference,
                unit=data.get('unit'),
                description=data.get('description')
            )
            
            log_success(f"Created product: {reference} - {name}")
            session.add(product)
            session.commit()
            
            return jsonify(serialize_model(product)), 201
    except Exception as e:
        print(f"ERROR creating product: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/products/batch', methods=['POST'])
def create_products_batch():
    """Create multiple products in a single transaction (10-100x faster)"""
    try:
        data = request.json
        
        if not isinstance(data, list):
            return jsonify({'error': 'Expected a list of products'}), 400
        
        if len(data) == 0:
            return jsonify({'error': 'Product list is empty'}), 400
        
        # Validate all products before insertion
        for i, item in enumerate(data):
            if not item.get('name'):
                return jsonify({'error': f'Product {i}: name is required'}), 400
            if not item.get('reference'):
                return jsonify({'error': f'Product {i}: reference is required'}), 400
        
        with db_manager.get_session() as session:
            products = []
            for item in data:
                product = Product(
                    name=item['name'],
                    reference=item['reference'],
                    unit=item.get('unit'),
                    description=item.get('description')
                )
                products.append(product)
            
            session.bulk_save_objects(products, return_defaults=True)
            log_success(f"Batch created {len(products)} products")
            session.commit()
            
            return jsonify({
                'message': f'Successfully created {len(products)} products',
                'count': len(products)
            }), 201
    except Exception as e:
        print(f"ERROR creating products batch: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update existing product"""
    try:
        data = request.json
        with db_manager.get_session() as session:
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
    except Exception as e:        return jsonify({'error': str(e)}), 400


@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete product"""
    try:
        with db_manager.get_session() as session:
            product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        session.delete(product)
        session.commit()
        
        return jsonify({'message': 'Product deleted successfully'})
    except Exception as e:        return jsonify({'error': str(e)}), 400


# ==================== PURCHASE ORDER ENDPOINTS ====================

@app.route('/purchase_orders', methods=['GET'])
def get_purchase_orders():
    """Get all purchase orders"""
    try:
        with db_manager.get_session() as session:
            # Eager load product relationship to avoid DetachedInstanceError
            from sqlalchemy.orm import joinedload
            orders = session.query(PurchaseOrder).options(joinedload(PurchaseOrder.product)).all()
        return jsonify(serialize_list(orders))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/purchase_orders/<int:order_id>', methods=['GET'])
def get_purchase_order(order_id):
    """Get purchase order by ID"""
    try:
        with db_manager.get_session() as session:
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
        return jsonify({'error': str(e)}), 500


@app.route('/purchase_orders/<int:order_id>', methods=['PUT'])
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
        return jsonify({'error': str(e)}), 500


@app.route('/purchase_orders/<int:order_id>', methods=['DELETE'])
def delete_purchase_order(order_id):
    """Delete purchase order"""
    try:
        with db_manager.get_session() as session:
            order = session.query(PurchaseOrder).filter_by(id=order_id).first()
        if not order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        session.delete(order)
        session.commit()
        
        return jsonify({'message': 'Purchase order deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== PURCHASE (SUPPLIER INVOICE) ENDPOINTS ====================

@app.route('/purchases', methods=['GET'])
def get_purchases():
    """Get all supplier purchases"""
    try:
        with db_manager.get_session() as session:
            purchases = session.query(Purchase).all()
            return jsonify([serialize_model(p) for p in purchases])
    except Exception as e:
        print(f"ERROR getting purchases: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/purchases/<int:purchase_id>', methods=['GET'])
def get_purchase(purchase_id):
    """Get purchase by ID"""
    try:
        with db_manager.get_session() as session:
            purchase = session.query(Purchase).filter_by(id=purchase_id).first()
            if not purchase:
                return jsonify({'error': 'Purchase not found'}), 404
            return jsonify(serialize_model(purchase))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/purchases', methods=['POST'])
def create_purchase():
    """Create new supplier purchase"""
    try:
        data = request.get_json()
        with db_manager.get_session() as session:
            # Fetch the related PO and check stock
            po = session.query(PurchaseOrder).filter(PurchaseOrder.id == data['purchase_order_id']).with_for_update().first()
            if not po:
                return jsonify({'error': 'PurchaseOrder not found'}), 400
            if data['quantity'] > po.remaining_stock:
                return jsonify({'error': f'Not enough remaining stock in PO. Available: {po.remaining_stock}, Requested: {data["quantity"]}'}, 400)
            # Decrement PO stock
            po.remaining_stock -= data['quantity']
            purchase = Purchase(
                invoice_number=data['invoice_number'],
                purchase_order_id=data['purchase_order_id'],
                product_id=data['product_id'],
                quantity=data['quantity'],
                remaining_stock=data.get('remaining_stock', data['quantity']),
                unit_price=data['unit_price'],
                total_price=data['total_price'],
                purchase_date=datetime.fromisoformat(data['purchase_date']) if 'purchase_date' in data else datetime.utcnow(),
                supplier_name=data.get('supplier_name'),
                notes=data.get('notes')
            )
            session.add(purchase)
            session.commit()
            return jsonify(serialize_model(purchase)), 201
    except Exception as e:
        print(f"ERROR creating purchase: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@app.route('/purchases/<int:purchase_id>', methods=['PUT'])
def update_purchase(purchase_id):
    """Update existing purchase"""
    try:
        data = request.get_json()
        with db_manager.get_session() as session:
            purchase = session.query(Purchase).filter_by(id=purchase_id).first()
            if not purchase:
                return jsonify({'error': 'Purchase not found'}), 404
            # Update all relevant fields
            if 'invoice_number' in data:
                purchase.invoice_number = data['invoice_number']
            if 'supplier_name' in data:
                purchase.supplier_name = data['supplier_name']
            if 'purchase_date' in data:
                try:
                    if isinstance(data['purchase_date'], str):
                        purchase.purchase_date = datetime.fromisoformat(data['purchase_date'])
                    else:
                        purchase.purchase_date = data['purchase_date']
                except Exception:
                    pass
            if 'quantity' in data:
                purchase.quantity = data['quantity']
            if 'remaining_stock' in data:
                purchase.remaining_stock = data['remaining_stock']
            if 'unit_price' in data:
                purchase.unit_price = data['unit_price']
            if 'total_price' in data:
                purchase.total_price = data['total_price']
            if 'notes' in data:
                purchase.notes = data['notes']
            purchase.updated_at = datetime.utcnow()
            session.commit()
            return jsonify(serialize_model(purchase))
    except Exception as e:
        print(f"ERROR updating purchase: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/purchases/<int:purchase_id>', methods=['DELETE'])
def delete_purchase(purchase_id):
    """Delete purchase"""
    try:
        with db_manager.get_session() as session:
            purchase = session.query(Purchase).filter_by(id=purchase_id).first()
        if not purchase:
            return jsonify({'error': 'Purchase not found'}), 404
        
        session.delete(purchase)
        session.commit()
        
        return jsonify({'message': 'Purchase deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== PHARMACY ENDPOINTS ====================

@app.route('/pharmacies', methods=['GET'])
def get_pharmacies():
    """Get all pharmacies"""
    try:
        with db_manager.get_session() as session:
            pharmacies = session.query(Pharmacy).all()
        return jsonify(serialize_list(pharmacies))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/pharmacies', methods=['POST'])
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
        return jsonify({'error': str(e)}), 500


@app.route('/pharmacies/<int:pharmacy_id>', methods=['PUT'])
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
        return jsonify({'error': str(e)}), 500


@app.route('/pharmacies/<int:pharmacy_id>', methods=['DELETE'])
def delete_pharmacy(pharmacy_id):
    """Delete pharmacy"""
    try:
        with db_manager.get_session() as session:
            pharmacy = session.query(Pharmacy).filter_by(id=pharmacy_id).first()
        if not pharmacy:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        session.delete(pharmacy)
        session.commit()
        
        return jsonify({'message': 'Pharmacy deleted successfully'})
    except Exception as e:        return jsonify({'error': str(e)}), 400


# ==================== TRANSACTION ENDPOINTS ====================

@app.route('/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions with optional filtering"""
    try:
        with db_manager.get_session() as session:
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
        # Validate required fields
        required_fields = ['purchase_id', 'product_id', 'distribution_location_id', 'quantity']
        missing = [f for f in required_fields if f not in data]
        if missing:
            tb = traceback.format_exc()
            print(f"[API ERROR] /transactions (400)\nMissing fields: {missing}\n{tb}", file=sys.stderr, flush=True)
            return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

        with db_manager.get_session() as session:
            try:
                # Fetch the purchase (supplier invoice)
                purchase = session.query(Purchase).filter_by(id=data['purchase_id']).with_for_update().first()
                if not purchase:
                    return jsonify({'error': 'Purchase not found'}), 400
                if data['quantity'] > purchase.remaining_stock:
                    return jsonify({'error': f'Not enough remaining stock in supplier purchase. Available: {purchase.remaining_stock}, Requested: {data["quantity"]}'}, 400)

                # Deduct from supplier purchase remaining_stock
                purchase.remaining_stock -= data['quantity']

                # Update distribution location remaining_stock (if such a field exists)
                dist_loc = session.query(DistributionLocation).filter_by(id=data['distribution_location_id']).with_for_update().first()
                if not dist_loc:
                    return jsonify({'error': 'Distribution location not found'}), 400

                # If DistributionLocation has a remaining_stock field, update it
                if hasattr(dist_loc, 'remaining_stock'):
                    if dist_loc.remaining_stock is None:
                        dist_loc.remaining_stock = 0
                    dist_loc.remaining_stock += data['quantity']

                transaction_kwargs = {
                    'purchase_id': data['purchase_id'],
                    'product_id': data['product_id'],
                    'distribution_location_id': data['distribution_location_id'],
                    'quantity': data['quantity'],
                    'transaction_date': datetime.fromisoformat(data['transaction_date']) if 'transaction_date' in data and data['transaction_date'] else datetime.utcnow(),
                    'notes': data.get('notes'),
                }
                if 'transaction_reference' in data:
                    transaction_kwargs['transaction_reference'] = data['transaction_reference']

                transaction = Transaction(**transaction_kwargs)
                session.add(transaction)
                session.commit()
                return jsonify(serialize_model(transaction)), 201
            except Exception as e:
                tb = traceback.format_exc()
                print(f"[API ERROR] /transactions (400)\n{e}\n{tb}", file=sys.stderr, flush=True)
                return jsonify({'error': str(e), 'traceback': tb}), 400
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[API ERROR] /transactions (500)\n{e}\n{tb}", file=sys.stderr, flush=True)
        return jsonify({'error': str(e), 'traceback': tb}), 500


@app.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Delete transaction"""
    try:
        with db_manager.get_session() as session:
            transaction = session.query(Transaction).filter_by(id=transaction_id).first()
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        session.delete(transaction)
        session.commit()
        
        return jsonify({'message': 'Transaction deleted successfully'})
    except Exception as e:        return jsonify({'error': str(e)}), 400


# ==================== ACTIVITY LOG ENDPOINTS ====================

@app.route('/activity_logs', methods=['GET'])
def get_activity_logs():
    """Get activity logs with optional filtering"""
    try:
        with db_manager.get_session() as session:
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
        return jsonify({'error': str(e)}), 500


# ==================== DISTRIBUTION LOCATION ENDPOINTS ====================

@app.route('/distribution_locations', methods=['GET'])
def get_distribution_locations():
    """Get all distribution locations"""
    try:
        with db_manager.get_session() as session:
            locations = session.query(DistributionLocation).all()
        return jsonify(serialize_list(locations))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/distribution_locations', methods=['POST'])
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
        return jsonify({'error': str(e)}), 500


@app.route('/distribution_locations/<int:location_id>', methods=['DELETE'])
def delete_distribution_location(location_id):
    """Delete distribution location"""
    try:
        with db_manager.get_session() as session:
            location = session.get(DistributionLocation, location_id)
            if not location:
                return jsonify({'error': 'Distribution location not found'}), 404
            
            session.delete(location)
            session.commit()
            
        return jsonify({'message': f'Distribution location {location_id} deleted successfully'}), 200
    except Exception as e:
        print(f"ERROR deleting distribution location: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/distribution_locations/<int:location_id>', methods=['PUT'])
def update_distribution_location(location_id):
    """Update existing distribution location"""
    try:
        data = request.json
        with db_manager.get_session() as session:
            location = session.get(DistributionLocation, location_id)
            if not location:
                return jsonify({'error': 'Distribution location not found'}), 404

            # Update fields if present
            if 'name' in data:
                location.name = data['name']
            if 'reference' in data:
                location.reference = data['reference']
            if 'trn' in data:
                location.trn = data['trn']
            if 'pharmacy_id' in data:
                location.pharmacy_id = data['pharmacy_id']
            if 'address' in data:
                location.address = data['address']
            if 'contact_person' in data:
                location.contact_person = data['contact_person']
            if 'phone' in data:
                location.phone = data['phone']

            location.updated_at = datetime.utcnow() if hasattr(location, 'updated_at') else location.updated_at
            session.commit()
            return jsonify(serialize_model(location)), 200
    except Exception as e:
        print(f"ERROR updating distribution location: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== MEDICAL CENTRE ENDPOINTS ====================

@app.route('/medical_centres', methods=['GET'])
def get_medical_centres():
    """Get all medical centres"""
    try:
        with db_manager.get_session() as session:
            centres = session.query(MedicalCentre).all()
        return jsonify(serialize_list(centres))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/medical_centres', methods=['POST'])
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
        return jsonify({'error': str(e)}), 500


# ==================== MEDICAL CENTRE UPDATE ENDPOINT ====================
@app.route('/medical_centres/<int:centre_id>', methods=['PUT'])
def update_medical_centre(centre_id):
    """Update existing medical centre"""
    try:
        data = request.json
        with db_manager.get_session() as session:
            centre = session.get(MedicalCentre, centre_id)
            if not centre:
                return jsonify({'error': 'Medical centre not found'}), 404

            # Update fields if present
            if 'name' in data:
                centre.name = data['name']
            if 'reference' in data:
                centre.reference = data['reference']
            if 'address' in data:
                centre.address = data['address']
            if 'contact_person' in data:
                centre.contact_person = data['contact_person']
            if 'phone' in data:
                centre.phone = data['phone']

            centre.updated_at = datetime.utcnow() if hasattr(centre, 'updated_at') else centre.updated_at
            session.commit()
            return jsonify(serialize_model(centre)), 200
    except Exception as e:
        print(f"ERROR updating medical centre: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/medical_centres/<int:centre_id>', methods=['DELETE'])
def delete_medical_centre(centre_id):
    """Delete medical centre"""
    try:
        with db_manager.get_session() as session:
            centre = session.get(MedicalCentre, centre_id)
            if not centre:
                return jsonify({'error': 'Medical centre not found'}), 404
            
            session.delete(centre)
            session.commit()
            
        return jsonify({'message': f'Medical centre {centre_id} deleted successfully'}), 200
    except Exception as e:
        print(f"ERROR deleting medical centre: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== PATIENT COUPON ENDPOINTS ====================

@app.route('/patient_coupons', methods=['GET'])
def get_patient_coupons():
    """Get all patient coupons"""
    try:
        with db_manager.get_session() as session:
            coupons = session.query(PatientCoupon).all()
        log_request('/patient_coupons', f"- Retrieved {len(coupons)} coupons")
        return jsonify(serialize_list(coupons))
    except Exception as e:
        tb = traceback.format_exc()
        print(f"\n[SERVER ERROR] /patient_coupons\n{tb}\n", flush=True)
        return jsonify({'error': str(e), 'traceback': tb}), 500


@app.route('/patient_coupons', methods=['POST'])
def create_patient_coupon():
    """Create new patient coupon"""
    try:
        data = request.json
        
        # Required fields
        if 'coupon_reference' not in data:
            return jsonify({'error': 'coupon_reference is required'}), 400
        if 'medical_centre_id' not in data:
            return jsonify({'error': 'medical_centre_id is required'}), 400
        if 'distribution_location_id' not in data:
            return jsonify({'error': 'distribution_location_id is required'}), 400
        if 'quantity_pieces' not in data:
            return jsonify({'error': 'quantity_pieces is required'}), 400
        if 'date_received' not in data:
            return jsonify({'error': 'date_received is required'}), 400
        
        with db_manager.get_session() as session:
            coupon = PatientCoupon(
                coupon_reference=data['coupon_reference'],
                patient_name=data.get('patient_name'),
                cpr=data.get('cpr'),
                quantity_pieces=data['quantity_pieces'],
                medical_centre_id=data['medical_centre_id'],
                distribution_location_id=data['distribution_location_id'],
                product_id=data.get('product_id'),
                verified=data.get('verified', False),
                verification_reference=data.get('verification_reference'),
                delivery_note_number=data.get('delivery_note_number'),
                grv_reference=data.get('grv_reference'),
                date_received=datetime.fromisoformat(data['date_received']),
                date_verified=datetime.fromisoformat(data['date_verified']) if data.get('date_verified') else None,
                notes=data.get('notes')
            )
            
            session.add(coupon)
            session.commit()
            
            return jsonify(serialize_model(coupon)), 201
    except Exception as e:
        print(f"ERROR creating patient coupon: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/patient_coupons/batch', methods=['POST'])
def create_patient_coupons_batch():
    """Create multiple patient coupons in a single transaction (10-100x faster)"""
    try:
        data = request.json
        
        if not isinstance(data, list):
            return jsonify({'error': 'Expected a list of coupons'}), 400
        
        if len(data) == 0:
            return jsonify({'error': 'Coupon list is empty'}), 400
        
        # Validate all coupons before insertion
        for i, item in enumerate(data):
            if 'coupon_reference' not in item:
                return jsonify({'error': f'Coupon {i}: coupon_reference is required'}), 400
            if 'medical_centre_id' not in item:
                return jsonify({'error': f'Coupon {i}: medical_centre_id is required'}), 400
            if 'distribution_location_id' not in item:
                return jsonify({'error': f'Coupon {i}: distribution_location_id is required'}), 400
            if 'quantity_pieces' not in item:
                return jsonify({'error': f'Coupon {i}: quantity_pieces is required'}), 400
            if 'date_received' not in item:
                return jsonify({'error': f'Coupon {i}: date_received is required'}), 400
        
        with db_manager.get_session() as session:
            coupons = []
            for item in data:
                coupon = PatientCoupon(
                    coupon_reference=item['coupon_reference'],
                    patient_name=item.get('patient_name'),
                    cpr=item.get('cpr'),
                    quantity_pieces=item['quantity_pieces'],
                    medical_centre_id=item['medical_centre_id'],
                    distribution_location_id=item['distribution_location_id'],
                    product_id=item.get('product_id'),
                    verified=item.get('verified', False),
                    verification_reference=item.get('verification_reference'),
                    delivery_note_number=item.get('delivery_note_number'),
                    grv_reference=item.get('grv_reference'),
                    date_received=datetime.fromisoformat(item['date_received']),
                    date_verified=datetime.fromisoformat(item['date_verified']) if item.get('date_verified') else None,
                    notes=item.get('notes')
                )
                coupons.append(coupon)
            
            session.bulk_save_objects(coupons, return_defaults=True)
            log_success(f"Batch created {len(coupons)} coupons")
            session.commit()
            
            return jsonify({
                'message': f'Successfully created {len(coupons)} coupons',
                'count': len(coupons)
            }), 201
    except Exception as e:
        print(f"ERROR creating coupons batch: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/patient_coupons/<int:id>', methods=['DELETE'])
def delete_patient_coupon(id):
    """Delete patient coupon"""
    try:
        with db_manager.get_session() as session:
            coupon = session.get(PatientCoupon, id)
            if not coupon:
                return jsonify({'error': 'Patient coupon not found'}), 404
            
            session.delete(coupon)
            session.commit()
            return jsonify({'message': 'Patient coupon deleted successfully'}), 200
    except Exception as e:
        print(f"ERROR deleting patient coupon: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500



# ==================== PATIENT COUPON UPDATE ENDPOINT ====================

@app.route('/patient_coupons/<int:id>', methods=['PUT'])
def update_patient_coupon(id):
    """Update existing patient coupon"""
    try:
        data = request.json
        with db_manager.get_session() as session:
            coupon = session.get(PatientCoupon, id)
            if not coupon:
                return jsonify({'error': 'Patient coupon not found'}), 404

            # Update fields if present
            if 'coupon_reference' in data:
                coupon.coupon_reference = data['coupon_reference']
            if 'patient_name' in data:
                coupon.patient_name = data['patient_name']
            if 'cpr' in data:
                coupon.cpr = data['cpr']
            if 'quantity_pieces' in data:
                coupon.quantity_pieces = data['quantity_pieces']
            if 'medical_centre_id' in data:
                coupon.medical_centre_id = data['medical_centre_id']
            if 'distribution_location_id' in data:
                coupon.distribution_location_id = data['distribution_location_id']
            if 'product_id' in data:
                coupon.product_id = data['product_id']
            if 'verified' in data:
                coupon.verified = data['verified']
            if 'verification_reference' in data:
                coupon.verification_reference = data['verification_reference']
            if 'delivery_note_number' in data:
                coupon.delivery_note_number = data['delivery_note_number']
            if 'grv_reference' in data:
                coupon.grv_reference = data['grv_reference']
            if 'date_received' in data:
                try:
                    if isinstance(data['date_received'], str):
                        coupon.date_received = datetime.fromisoformat(data['date_received'])
                    else:
                        coupon.date_received = data['date_received']
                except Exception:
                    pass
            if 'date_verified' in data:
                try:
                    if data['date_verified']:
                        if isinstance(data['date_verified'], str):
                            coupon.date_verified = datetime.fromisoformat(data['date_verified'])
                        else:
                            coupon.date_verified = data['date_verified']
                    else:
                        coupon.date_verified = None
                except Exception:
                    pass
            if 'notes' in data:
                coupon.notes = data['notes']

            coupon.updated_at = datetime.utcnow() if hasattr(coupon, 'updated_at') else coupon.updated_at
            session.commit()
            return jsonify(serialize_model(coupon)), 200
    except Exception as e:
        print(f"ERROR updating patient coupon: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== STATISTICS ENDPOINTS ====================

@app.route('/statistics/inventory', methods=['GET'])
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
        return jsonify({'error': str(e)}), 500


# ==================== SERVER STARTUP ====================

def get_local_ip():
    """Get the local IP address of the server"""
    import socket
    try:
        # Create a socket connection to determine local IP
        # This doesn't actually connect, just determines which interface would be used
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Fallback to localhost if unable to determine
        return "127.0.0.1"


def main():
    """Start the API server"""
    print("=" * 60)
    print("Alnoor Medical Services - API Server")
    print("=" * 60)
    print()
    
    # Setup logging first
    setup_logging()
    
    # Initialize database
    init_db()
    
    # Get server configuration
    host = os.environ.get('ALNOOR_API_HOST', '0.0.0.0')
    port = int(os.environ.get('ALNOOR_API_PORT', 5000))
    
    # Get actual local IP address
    local_ip = get_local_ip()
    
    print(f"🚀 Starting PRODUCTION server...")
    print(f"📍 Server Address: http://{local_ip}:{port}")
    print(f"📊 Health Check: http://{local_ip}:{port}/health")
    print()
    print("ℹ️  Server Mode: Production (Multi-user support enabled)")
    print("ℹ️  Max Concurrent Users: 10+ simultaneous connections")
    print("ℹ️  Threads: 12 | Connection Limit: 100")
    print()
    
    if ENABLE_LOGGING:
        print("📝 Request Logging: ✅ ENABLED")
        print("   • Client connections tracked")
        print("   • Request/response logged with timing")
        print("   • Logs: logs/api_server_YYYYMMDD.log")
    else:
        print("📝 Request Logging: ⚪ DISABLED")
        print("   To enable: set ALNOOR_ENABLE_LOGGING=true before starting")
        print("   Example (PowerShell): $env:ALNOOR_ENABLE_LOGGING='true'; python src\\api_server.py")
    print()
    print("📋 CLIENT CONFIGURATION:")
    print(f"   config.ini setting: server_url = http://{local_ip}:{port}")
    print()
    print("⌨️  Press Ctrl+C to stop server")
    print("=" * 60)
    print()
    
    if ENABLE_LOGGING:
        app.logger.info(f"🌐 Server listening on {local_ip}:{port}")
        app.logger.info(f"⏳ Waiting for client connections...")
        app.logger.info("")
    
    try:
        # Use Waitress production server (Windows-friendly)
        from waitress import serve
        # Note: Waitress will still show 0.0.0.0 in its own logs, but our logs show real IP
        if ENABLE_LOGGING:
            print(f"✅ Server running on {local_ip}:{port}")
            print("   (Waitress may show 0.0.0.0 - this is normal, clients use {})\n".format(local_ip))
        serve(app, host=host, port=port, threads=12, channel_timeout=300, connection_limit=100)
    except ImportError:
        # Fallback to Flask dev server if Waitress not installed
        print("⚠️  WARNING: Waitress not installed, using development server")
        print("⚠️  For production use, install: pip install waitress")
        print()
        app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
