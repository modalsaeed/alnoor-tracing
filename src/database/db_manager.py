"""
Database Manager for Alnoor Medical Services Tracking App.

Handles database connection, session management, initialization,
and provides helper methods for common database operations.
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Type, TypeVar, List
from contextlib import contextmanager

from sqlalchemy import create_engine, event
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
)

# Type variable for generic operations
T = TypeVar('T')


class DatabaseManager:
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
    
    def _initialize_engine(self):
        """Create SQLAlchemy engine with SQLite-specific settings."""
        # Create engine with connection pooling and foreign key support
        self._engine = create_engine(
            f'sqlite:///{self.db_path}',
            echo=False,  # Set to True for SQL query debugging
            future=True,
            pool_pre_ping=True,
        )
        
        # Enable foreign key constraints for SQLite
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        # Create session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )
    
    def _initialize_database(self):
        """Create all tables if they don't exist."""
        Base.metadata.create_all(self._engine)
    
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
    
    def update(self, record: T) -> T:
        """Update an existing record."""
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
    return DatabaseManager(db_path)
