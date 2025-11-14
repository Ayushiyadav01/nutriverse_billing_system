from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3
import os

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _add_missing_columns():
    """Add missing columns to existing SQLite database"""
    if "sqlite" not in settings.DATABASE_URL.lower():
        return  # Only for SQLite
    
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    # Handle relative paths - make absolute if needed
    if not os.path.isabs(db_path):
        # If relative, it's relative to the current working directory
        # For SQLite, relative paths work fine, but let's ensure the directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    if not os.path.exists(db_path):
        return  # Database doesn't exist yet, will be created
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add is_deleted column if it doesn't exist
        if 'is_deleted' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL")
        
        # Add deleted_at column if it doesn't exist
        if 'deleted_at' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN deleted_at DATETIME")
        
        # Add food_preparation_stage column if it doesn't exist
        if 'food_preparation_stage' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN food_preparation_stage VARCHAR(20) DEFAULT 'ordered'")
        
        # Add payment_status column if it doesn't exist
        if 'payment_status' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(20) DEFAULT 'pending'")
        
        # Add payment_completed_at column if it doesn't exist
        if 'payment_completed_at' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN payment_completed_at DATETIME")
        
        conn.commit()
        conn.close()
    except Exception as e:
        # If migration fails, just continue - columns might already exist or table might not exist
        pass

def init_db():
    Base.metadata.create_all(bind=engine)
    # Add missing columns to existing databases
    _add_missing_columns()

