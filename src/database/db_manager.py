"""
Database Manager for Alnoor Medical Services Tracking App.

Handles database connection, session management, initialization,
and provides helper methods for common database operations.

Supports both local SQLite mode and remote API client mode.
"""

import os
import sys
import shutil
import configparser
from datetime import datetime
from pathlib import Path
from typing import Optional, Type, TypeVar, List
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.engine import Engine

from .models import (
    Base,
    Product,
    PurchaseOrder,
    Purchase,
    Pharmacy,
    DistributionLocation,
    MedicalCentre,
    PatientCoupon,
    Transaction,
    ActivityLog,
    DeliveryNote,
)

# Type variable for generic operations
T = TypeVar('T')


# Global variable to store connection info for display
_connection_debug_info = []

def get_connection_debug_info():
    """Get the connection debug information collected during initialization"""
    return _connection_debug_info

def get_database_instance(db_path: Optional[str] = None):
    """
    Factory function to get the appropriate database instance.
    Returns DatabaseClient if configured for API mode, otherwise DatabaseManager.
    """
    global _connection_debug_info
    _connection_debug_info = []
    
    def add_debug(msg):
        """Add debug message to global list"""
        _connection_debug_info.append(msg)
    
    # Check for API client mode in config
    if db_path is None:
        if getattr(sys, 'frozen', False):
            config_path = Path(sys.executable).parent / 'config.ini'
        else:
            config_path = Path(__file__).parent.parent.parent / 'config.ini'
        
        add_debug(f"🔍 Config path: {config_path}")
        add_debug(f"🔍 Config exists: {config_path.exists()}")
        
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            
            add_debug(f"🔍 Config sections: {config.sections()}")
            
            # Check for API server mode
            if 'server' in config:
                add_debug(f"🔍 [server] section found")
                mode = config['server'].get('mode', 'NOT SET')
                server_url = config['server'].get('server_url', 'NOT SET')
                add_debug(f"🔍 mode = {mode}")
                add_debug(f"🔍 server_url = {server_url}")
                
                if mode == 'client':
                    # Use API client instead of direct database
                    server_url = config['server'].get('server_url', 'http://localhost:5000')
                    add_debug(f"✅ Using API CLIENT mode")
                    add_debug(f"🌐 Server: {server_url}")
                    from .db_client import DatabaseClient
                    return DatabaseClient(server_url)
                else:
                    add_debug(f"⚠️  mode is '{mode}', not 'client'")
            else:
                add_debug(f"⚠️  No [server] section in config")
        else:
            add_debug(f"⚠️  Config file not found")
    
    # Default: use local SQLite database
    add_debug(f"✅ Using LOCAL DATABASE mode")
    return DatabaseManager(db_path)


class DatabaseManager:

    def create(self, model_class, data_dict):
        """
        Create a new record from a dict of fields, for compatibility with API client signature.
        Args:
            model_class: The ORM model class to create.
            data_dict: Dict of field values.
        Returns:
            The created ORM object.
        """
        with self.get_session() as session:
            record = model_class(**data_dict)
            session.add(record)
            session.flush()
            session.refresh(record)
            session.commit()  # Ensure changes are committed to DB
            self.log_activity(
                'CREATE',
                getattr(model_class, '__tablename__', str(model_class)),
                getattr(record, 'id', 0),
                f'Created new {model_class.__name__} (ID: {getattr(record, "id", 0)})',
            )
            return record
            self.log_activity(
                'CREATE',
                getattr(model_class, '__tablename__', str(model_class)),
                getattr(record, 'id', 0),
                f'Created new {model_class.__name__} (ID: {getattr(record, "id", 0)})',
            )
            return record
    def create_patient_coupons_batch(self, coupons: list) -> dict:
        """
        Bulk insert multiple patient coupons.
        Args:
            coupons: List of dicts with coupon fields (coupon_reference, patient_name, etc.)
        Returns:
            Dict with 'success' and 'created' keys, and 'errors' if any failures.
        """
        created = []
        errors = []
        with self.get_session() as session:
            for idx, coupon_data in enumerate(coupons):
                try:
                    # Defensive: ensure required fields
                    coupon_reference = coupon_data.get('coupon_reference')
                    if not coupon_reference:
                        raise ValueError('Missing coupon_reference')
                    # Convert date fields if present
                    date_received = coupon_data.get('date_received')
                    if date_received and isinstance(date_received, str):
                        try:
                            date_received = datetime.fromisoformat(date_received)
                        except Exception:
                            date_received = None
                    date_verified = coupon_data.get('date_verified')
                    if date_verified and isinstance(date_verified, str):
                        try:
                            date_verified = datetime.fromisoformat(date_verified)
                        except Exception:
                            date_verified = None
                    # Create PatientCoupon instance
                    coupon = PatientCoupon(
                        coupon_reference=coupon_reference,
                        patient_name=coupon_data.get('patient_name'),
                        cpr=coupon_data.get('cpr'),
                        quantity_pieces=coupon_data.get('quantity_pieces', 1),
                        medical_centre_id=coupon_data.get('medical_centre_id'),
                        distribution_location_id=coupon_data.get('distribution_location_id'),
                        product_id=coupon_data.get('product_id'),
                        verified=coupon_data.get('verified', False),
                        verification_reference=coupon_data.get('verification_reference'),
                        delivery_note_number=coupon_data.get('delivery_note_number'),
                        grv_reference=coupon_data.get('grv_reference'),
                        date_received=date_received,
                        date_verified=date_verified,
                        notes=coupon_data.get('notes'),
                    )
                    session.add(coupon)
                    session.flush()
                    created.append({
                        'id': coupon.id,
                        'coupon_reference': coupon.coupon_reference
                    })
                except Exception as e:
                    errors.append({'index': idx, 'error': str(e), 'data': coupon_data})
            # No explicit session.commit() needed; context manager handles commit/rollback
        result = {'success': len(errors) == 0, 'created': created}
        if errors:
            result['errors'] = errors
        return result

    """
    Manages database connections and operations.
    Singleton pattern to ensure single database instance.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None
    
    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if self._engine is not None:
            return  # Already initialized
        
        if db_path is None:
            # Check for test database environment variable
            test_db = os.environ.get('ALNOOR_TEST_DB')
            if test_db:
                db_path = test_db
                print(f"Using TEST database: {db_path}")
            else:
                # Check for config.ini file (for network deployment)
                config_path = self._get_config_path()
                if config_path and config_path.exists():
                    config = configparser.ConfigParser()
                    config.read(config_path, encoding='utf-8')
                    if 'database' in config and 'path' in config['database']:
                        db_path = config['database']['path']
                        print(f"Using database from config.ini: {db_path}")
                
                # If no config or no database path in config, use defaults
                if not db_path:
                    # Determine if running as frozen executable (PyInstaller) or as script
                    if getattr(sys, 'frozen', False):
                        # Running as compiled executable
                        # Use user's AppData directory for database
                        app_name = 'Alnoor Medical Services'
                        if sys.platform == 'win32':
                            # Windows: Use LOCALAPPDATA
                            app_data = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
                            data_dir = app_data / app_name / 'database'
                        elif sys.platform == 'darwin':
                            # macOS: Use ~/Library/Application Support
                            data_dir = Path.home() / 'Library' / 'Application Support' / app_name / 'database'
                        else:
                            # Linux: Use ~/.local/share
                            data_dir = Path.home() / '.local' / 'share' / app_name / 'database'
                    else:
                        # Running as script in development
                        # Use data/ folder in project root
                        project_root = Path(__file__).parent.parent.parent
                        data_dir = project_root / 'data'
                    
                    data_dir.mkdir(parents=True, exist_ok=True)
                    db_path = str(data_dir / 'alnoor.db')
        
        self.db_path = db_path
        self._initialize_engine()
        self._initialize_database()
    
    def _get_config_path(self) -> Optional[Path]:
        """Get the path to config.ini file."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable - config.ini should be next to the exe
            return Path(sys.executable).parent / 'config.ini'
        else:
            # Running as script - config.ini in project root
            return Path(__file__).parent.parent.parent / 'config.ini'
    
    def _initialize_engine(self):
        """Create SQLAlchemy engine with SQLite-specific settings."""
        # Create engine with connection pooling and foreign key support
        self._engine = create_engine(
            f'sqlite:///{self.db_path}',
            echo=False,  # Set to True for SQL query debugging
            pool_size=20,           # Increased from default 5
            max_overflow=40,        # Increased from default 10
            pool_timeout=10,        # Lower timeout for faster error recovery
            future=True,
            pool_pre_ping=True,
            connect_args={
                'timeout': 60,  # 60 second timeout for locked database (network stability)
                'check_same_thread': False,  # Allow multi-threaded access
            },
        )
        
        # Enable foreign key constraints and WAL mode for SQLite
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
            cursor.execute("PRAGMA busy_timeout=60000")  # 60 second busy timeout for network stability
            cursor.execute("PRAGMA synchronous=NORMAL")  # Balance safety and performance
            cursor.close()
        
        # Create session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )
    
    def _initialize_database(self):
        """Create all tables if they don't exist, and run migrations if needed."""
        Base.metadata.create_all(self._engine)
        self._run_migrations()
    
    def _run_migrations(self):
        """Check database schema and apply migrations if needed."""
        try:
            # Use raw connection for migrations to avoid circular dependencies
            with self._engine.connect() as connection:
                # Check if products table has 'unit' column
                result = connection.execute(text("PRAGMA table_info(products)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'unit' not in columns:
                    print("Migrating database: Adding 'unit' column to products...")
                    connection.execute(text("ALTER TABLE products ADD COLUMN unit VARCHAR(50)"))
                    connection.commit()
                
                # Check if pharmacies table exists
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='pharmacies'"))
                if not result.fetchone():
                    print("Migrating database: Creating pharmacies table...")
                    connection.execute(text("""
                        CREATE TABLE pharmacies (
                            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(100) NOT NULL UNIQUE,
                            reference VARCHAR(50) NOT NULL UNIQUE,
                            contact_person VARCHAR(100),
                            phone VARCHAR(20),
                            email VARCHAR(100),
                            notes TEXT,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    connection.execute(text("CREATE INDEX ix_pharmacies_reference ON pharmacies (reference)"))
                    connection.commit()
                
                # Check if distribution_locations has pharmacy_id column
                result = connection.execute(text("PRAGMA table_info(distribution_locations)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'pharmacy_id' not in columns:
                    print("Migrating database: Adding 'pharmacy_id' to distribution_locations...")
                    connection.execute(text("ALTER TABLE distribution_locations ADD COLUMN pharmacy_id INTEGER REFERENCES pharmacies(id)"))
                    connection.commit()
                
                # Check if transactions has purchase_id column (renamed from purchase_order_id)
                result = connection.execute(text("PRAGMA table_info(transactions)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'purchase_id' not in columns:
                    print("Migrating database: Adding 'purchase_id' to transactions...")
                    connection.execute(text("ALTER TABLE transactions ADD COLUMN purchase_id INTEGER REFERENCES purchases(id)"))
                    connection.commit()
                
                # Check if patient_coupons has delivery_note_number and grv_reference columns
                result = connection.execute(text("PRAGMA table_info(patient_coupons)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'delivery_note_number' not in columns:
                    print("Migrating database: Adding 'delivery_note_number' to patient_coupons...")
                    connection.execute(text("ALTER TABLE patient_coupons ADD COLUMN delivery_note_number VARCHAR(100)"))
                    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_patient_coupons_delivery_note ON patient_coupons (delivery_note_number)"))
                    connection.commit()
                
                if 'grv_reference' not in columns:
                    print("Migrating database: Adding 'grv_reference' to patient_coupons...")
                    connection.execute(text("ALTER TABLE patient_coupons ADD COLUMN grv_reference VARCHAR(100)"))
                    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_patient_coupons_grv_reference ON patient_coupons (grv_reference)"))
                    connection.commit()
                
                # Check if pharmacies has trn column
                result = connection.execute(text("PRAGMA table_info(pharmacies)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'trn' not in columns:
                    print("Migrating database: Adding 'trn' to pharmacies...")
                    connection.execute(text("ALTER TABLE pharmacies ADD COLUMN trn VARCHAR(100)"))
                    connection.commit()
                
                # Check if distribution_locations has trn column
                result = connection.execute(text("PRAGMA table_info(distribution_locations)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'trn' not in columns:
                    print("Migrating database: Adding 'trn' to distribution_locations...")
                    connection.execute(text("ALTER TABLE distribution_locations ADD COLUMN trn VARCHAR(100)"))
                    connection.commit()
                
                # Check if reference columns are nullable (make optional)
                # For distribution_locations, medical_centres, pharmacies, and transactions
                result = connection.execute(text("PRAGMA table_info(distribution_locations)"))
                columns = {row[1]: row for row in result.fetchall()}
                
                # Check if reference column in distribution_locations is NOT NULL (notnull=1)
                if 'reference' in columns and columns['reference'][3] == 1:  # notnull field
                    print("Migrating database: Making distribution_locations.reference nullable...")
                    # Temporarily disable foreign keys for table recreation
                    connection.execute(text("PRAGMA foreign_keys=OFF"))
                    connection.execute(text("BEGIN TRANSACTION"))
                    
                    # Clean up any leftover temporary tables
                    connection.execute(text("DROP TABLE IF EXISTS distribution_locations_new"))
                    
                    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
                    connection.execute(text("""
                        CREATE TABLE distribution_locations_new (
                            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(255) NOT NULL,
                            reference VARCHAR(100),
                            trn VARCHAR(100),
                            pharmacy_id INTEGER,
                            address TEXT,
                            contact_person VARCHAR(255),
                            phone VARCHAR(50),
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            FOREIGN KEY(pharmacy_id) REFERENCES pharmacies (id)
                        )
                    """))
                    connection.execute(text("""
                        INSERT INTO distribution_locations_new 
                        SELECT id, name, reference, trn, pharmacy_id, address, contact_person, phone, created_at, updated_at
                        FROM distribution_locations
                    """))
                    connection.execute(text("DROP TABLE distribution_locations"))
                    connection.execute(text("ALTER TABLE distribution_locations_new RENAME TO distribution_locations"))
                    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_distribution_locations_reference ON distribution_locations (reference)"))
                    
                    connection.execute(text("COMMIT"))
                    connection.execute(text("PRAGMA foreign_keys=ON"))
                    connection.commit()
                
                # Check if reference column in medical_centres is NOT NULL
                result = connection.execute(text("PRAGMA table_info(medical_centres)"))
                columns = {row[1]: row for row in result.fetchall()}
                
                if 'reference' in columns and columns['reference'][3] == 1:  # notnull field
                    print("Migrating database: Making medical_centres.reference nullable...")
                    connection.execute(text("PRAGMA foreign_keys=OFF"))
                    connection.execute(text("BEGIN TRANSACTION"))
                    
                    connection.execute(text("""
                        CREATE TABLE medical_centres_new (
                            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(255) NOT NULL,
                            reference VARCHAR(100),
                            address TEXT,
                            contact_person VARCHAR(255),
                            phone VARCHAR(50),
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL
                        )
                    """))
                    connection.execute(text("""
                        INSERT INTO medical_centres_new 
                        SELECT id, name, reference, address, contact_person, phone, created_at, updated_at
                        FROM medical_centres
                    """))
                    connection.execute(text("DROP TABLE medical_centres"))
                    connection.execute(text("ALTER TABLE medical_centres_new RENAME TO medical_centres"))
                    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_medical_centres_reference ON medical_centres (reference)"))
                    
                    connection.execute(text("COMMIT"))
                    connection.execute(text("PRAGMA foreign_keys=ON"))
                    connection.commit()
                
                # Check if reference column in pharmacies is NOT NULL
                result = connection.execute(text("PRAGMA table_info(pharmacies)"))
                columns = {row[1]: row for row in result.fetchall()}
                
                if 'reference' in columns and columns['reference'][3] == 1:  # notnull field
                    print("Migrating database: Making pharmacies.reference nullable...")
                    connection.execute(text("PRAGMA foreign_keys=OFF"))
                    connection.execute(text("BEGIN TRANSACTION"))
                    
                    connection.execute(text("""
                        CREATE TABLE pharmacies_new (
                            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(255) NOT NULL,
                            reference VARCHAR(100),
                            trn VARCHAR(100),
                            contact_person VARCHAR(255),
                            phone VARCHAR(50),
                            email VARCHAR(255),
                            notes TEXT,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL
                        )
                    """))
                    connection.execute(text("""
                        INSERT INTO pharmacies_new 
                        SELECT id, name, reference, trn, contact_person, phone, email, notes, created_at, updated_at
                        FROM pharmacies
                    """))
                    connection.execute(text("DROP TABLE pharmacies"))
                    connection.execute(text("ALTER TABLE pharmacies_new RENAME TO pharmacies"))
                    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_pharmacies_name ON pharmacies (name)"))
                    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_pharmacies_reference ON pharmacies (reference)"))
                    
                    connection.execute(text("COMMIT"))
                    connection.execute(text("PRAGMA foreign_keys=ON"))
                    connection.commit()
                
                # Check if transaction_reference column in transactions is NOT NULL
                result = connection.execute(text("PRAGMA table_info(transactions)"))
                columns = {row[1]: row for row in result.fetchall()}
                
                if 'transaction_reference' in columns and columns['transaction_reference'][3] == 1:  # notnull field
                    print("Migrating database: Making transactions.transaction_reference nullable...")
                    connection.execute(text("PRAGMA foreign_keys=OFF"))
                    connection.execute(text("BEGIN TRANSACTION"))
                    
                    # This is more complex due to foreign keys, but we'll handle it
                    connection.execute(text("""
                        CREATE TABLE transactions_new (
                            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                            transaction_reference VARCHAR(100),
                            product_id INTEGER NOT NULL,
                            purchase_id INTEGER,
                            distribution_location_id INTEGER NOT NULL,
                            quantity INTEGER NOT NULL,
                            transaction_date DATETIME NOT NULL,
                            notes TEXT,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            FOREIGN KEY(product_id) REFERENCES products (id),
                            FOREIGN KEY(purchase_id) REFERENCES purchases (id),
                            FOREIGN KEY(distribution_location_id) REFERENCES distribution_locations (id)
                        )
                    """))
                    connection.execute(text("""
                        INSERT INTO transactions_new 
                        SELECT id, transaction_reference, product_id, purchase_id, distribution_location_id, 
                               quantity, transaction_date, notes, created_at, updated_at
                        FROM transactions
                    """))
                    connection.execute(text("DROP TABLE transactions"))
                    connection.execute(text("ALTER TABLE transactions_new RENAME TO transactions"))
                    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_transactions_transaction_reference ON transactions (transaction_reference)"))
                    
                    connection.execute(text("COMMIT"))
                    connection.execute(text("PRAGMA foreign_keys=ON"))
                    connection.commit()
                
        except Exception as e:
            print(f"Migration check failed: {e}")
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Usage:
            with db_manager.get_session() as session:
                session.query(Product).all()
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_backup(self, backup_dir: Optional[str] = None) -> str:
        """
        Create a backup of the database.
        
        Args:
            backup_dir: Directory to store backup. If None, uses default backups folder.
        
        Returns:
            Path to the backup file.
        """
        if backup_dir is None:
            project_root = Path(__file__).parent.parent.parent
            backup_dir = str(project_root / 'backups')
        
        Path(backup_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'alnoor_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(self.db_path, backup_path)
        
        # Log backup activity
        self.log_activity('BACKUP', 'database', 0, f'Database backup created: {backup_filename}')
        
        return backup_path
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore database from a backup file.
        
        Args:
            backup_path: Path to the backup file.
        
        Returns:
            True if successful, False otherwise.
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Create a backup of current database before restoring
        self.create_backup()
        
        # Close all connections
        self._engine.dispose()
        
        # Replace current database with backup
        shutil.copy2(backup_path, self.db_path)
        
        # Reinitialize engine
        self._initialize_engine()
        
        self.log_activity('RESTORE', 'database', 0, f'Database restored from: {os.path.basename(backup_path)}')
        
        return True
    
    def log_activity(
        self,
        action: str,
        table_name: str,
        record_id: int,
        description: str,
        old_values: Optional[str] = None,
        new_values: Optional[str] = None,
        user: Optional[str] = None,
    ):
        """
        Log an activity to the audit trail.
        
        Args:
            action: Type of action (CREATE, UPDATE, DELETE, etc.)
            table_name: Name of the affected table
            record_id: ID of the affected record
            description: Human-readable description
            old_values: JSON string of old values (for UPDATE)
            new_values: JSON string of new values (for CREATE/UPDATE)
            user: Username (for future multi-user support)
        """
        with self.get_session() as session:
            log = ActivityLog(
                action=action,
                table_name=table_name,
                record_id=record_id,
                description=description,
                old_values=old_values,
                new_values=new_values,
                user=user,
            )
            session.add(log)
    
    # Generic CRUD operations
    
    def get_all(self, model_class: Type[T]) -> List[T]:

        """Get all records of a model."""
        with self.get_session() as session:
            query = session.query(model_class)
            
            # Eagerly load relationships to avoid lazy loading issues
            if model_class == PurchaseOrder:
                query = query.options(joinedload(PurchaseOrder.product))
            elif model_class == Purchase:
                query = query.options(
                    joinedload(Purchase.purchase_order),
                    joinedload(Purchase.product)
                )
            elif model_class == Transaction:
                query = query.options(
                    joinedload(Transaction.product),
                    joinedload(Transaction.purchase),
                    joinedload(Transaction.distribution_location)
                )
            elif model_class == DistributionLocation:
                query = query.options(joinedload(DistributionLocation.pharmacy))
            elif model_class == PatientCoupon:
                query = query.options(
                    joinedload(PatientCoupon.product),
                    joinedload(PatientCoupon.medical_centre),
                    joinedload(PatientCoupon.distribution_location)
                )
            return query.all()
    
    def get_by_id(self, model_class: Type[T], record_id: int) -> Optional[T]:
        """Get a record by ID."""
        with self.get_session() as session:
            return session.query(model_class).filter(model_class.id == record_id).first()
    
    def add(self, record: T) -> T:
        """Add a new record to the database."""
        with self.get_session() as session:
            session.add(record)
            session.flush()  # Get the ID
            record_id = record.id
        
        # Log activity
        self.log_activity(
            'CREATE',
            record.__tablename__,
            record_id,
            f'Created new {record.__class__.__name__} (ID: {record_id})',
        )
        
        return record
    
    def update(self, *args, **kwargs):
        """
        Update an existing record.
        Supports both (record) and (model_class, record_id, update_fields) signatures for compatibility.
        """
        # Signature: update(record)
        if len(args) == 1 and not kwargs:
            record = args[0]
            with self.get_session() as session:
                session.merge(record)
                session.flush()
            # Log activity
            self.log_activity(
                'UPDATE',
                record.__tablename__,
                record.id,
                f'Updated {record.__class__.__name__} (ID: {record.id})',
            )
            return record
        # Signature: update(model_class, record_id, update_fields)
        elif len(args) == 3 and isinstance(args[2], dict):
            model_class, record_id, update_fields = args
            with self.get_session() as session:
                record = session.query(model_class).filter(model_class.id == record_id).first()
                if not record:
                    raise ValueError(f"Record with id {record_id} not found.")
                for k, v in update_fields.items():
                    setattr(record, k, v)
                session.flush()
            # Log activity
            self.log_activity(
                'UPDATE',
                getattr(model_class, '__tablename__', str(model_class)),
                record_id,
                f'Updated {model_class.__name__} (ID: {record_id})',
            )
            return record
        else:
            raise TypeError("update() must be called as update(record) or update(model_class, record_id, update_fields: dict)")
    
    def delete(self, model_class: Type[T], record_id: int) -> bool:
        """Delete a record by ID."""
        with self.get_session() as session:
            record = session.query(model_class).filter(model_class.id == record_id).first()
            if record:
                session.delete(record)
                
                # Log activity
                self.log_activity(
                    'DELETE',
                    model_class.__tablename__,
                    record_id,
                    f'Deleted {model_class.__name__} (ID: {record_id})',
                )
                return True
        return False
    
    def execute_raw_query(self, query: str):
        """Execute a raw SQL query (use with caution)."""
        with self._engine.connect() as conn:
            return conn.execute(query)
    
    def create_backup(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Optional custom backup path. If None, creates backup in backups folder.
            
        Returns:
            Path to the created backup file.
        """
        if backup_path is None:
            # Create backups folder next to database
            db_dir = Path(self.db_path).parent
            backups_dir = db_dir / 'backups'
            backups_dir.mkdir(exist_ok=True)
            
            # Create timestamped backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = str(backups_dir / f'alnoor_backup_{timestamp}.db')
        
        # Close any active connections and copy database file
        try:
            # Ensure all pending transactions are committed
            if self._engine:
                self._engine.dispose()
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Reinitialize engine after backup
            self._initialize_engine()
            
            return backup_path
        except Exception as e:
            # Reinitialize engine even if backup fails
            if self._engine is None:
                self._initialize_engine()
            raise Exception(f"Failed to create backup: {str(e)}")
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore database from a backup file.
        
        Args:
            backup_path: Path to the backup file.
            
        Returns:
            True if restore was successful.
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        try:
            # Close all connections
            if self._engine:
                self._engine.dispose()
            
            # Create a backup of current database before restoring
            current_backup = self.db_path + '.before_restore'
            shutil.copy2(self.db_path, current_backup)
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            
            # Reinitialize engine
            self._initialize_engine()
            
            return True
        except Exception as e:
            # Try to restore the pre-restore backup if restore failed
            if os.path.exists(current_backup):
                shutil.copy2(current_backup, self.db_path)
            
            # Reinitialize engine
            if self._engine is None:
                self._initialize_engine()
            
            raise Exception(f"Failed to restore backup: {str(e)}")
    
    def list_backups(self) -> List[dict]:
        """
        List all available backups.
        
        Returns:
            List of dictionaries containing backup information.
        """
        db_dir = Path(self.db_path).parent
        backups_dir = db_dir / 'backups'
        
        if not backups_dir.exists():
            return []
        
        backups = []
        for backup_file in backups_dir.glob('alnoor_backup_*.db'):
            stat = backup_file.stat()
            backups.append({
                'path': str(backup_file),
                'name': backup_file.name,
                'size_mb': stat.st_size / (1024 * 1024),
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
            })
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
    
    def get_database_info(self) -> dict:
        """Get information about the database."""
        with self.get_session() as session:
            info = {
                'db_path': self.db_path,
                'db_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0,
                'products_count': session.query(Product).count(),
                'purchase_orders_count': session.query(PurchaseOrder).count(),
                'distribution_locations_count': session.query(DistributionLocation).count(),
                'medical_centres_count': session.query(MedicalCentre).count(),
                'coupons_count': session.query(PatientCoupon).count(),
                'verified_coupons_count': session.query(PatientCoupon).filter(PatientCoupon.verified == True).count(),
                'transactions_count': session.query(Transaction).count(),
                'activity_logs_count': session.query(ActivityLog).count(),
            }
        return info
    
    def close(self):
        """Close database connection."""
        if self._engine:
            self._engine.dispose()


# Convenience function to get the global database manager instance
def get_db_manager(db_path: Optional[str] = None) -> DatabaseManager:
    """Get or create the global DatabaseManager instance."""
    return get_database_instance(db_path)
