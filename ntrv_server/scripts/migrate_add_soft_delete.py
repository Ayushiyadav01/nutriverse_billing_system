#!/usr/bin/env python3
"""
Migration script to add soft delete fields to Order table.
This script adds is_deleted and deleted_at columns if they don't exist.
"""

import sqlite3
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.db import engine

def migrate_database():
    """Add soft delete columns to Order table if using SQLite"""
    db_url = settings.DATABASE_URL
    
    if "sqlite" in db_url.lower():
        # Extract database path from SQLite URL
        db_path = db_url.replace("sqlite:///", "")
        
        if not os.path.exists(db_path):
            print(f"Database file {db_path} does not exist. Creating it...")
            from app.db import init_db
            init_db()
            print("Database created successfully!")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if columns exist
            cursor.execute("PRAGMA table_info(orders)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add is_deleted column if it doesn't exist
            if 'is_deleted' not in columns:
                print("Adding is_deleted column...")
                cursor.execute("ALTER TABLE orders ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL")
                print("✓ Added is_deleted column")
            else:
                print("✓ is_deleted column already exists")
            
            # Add deleted_at column if it doesn't exist
            if 'deleted_at' not in columns:
                print("Adding deleted_at column...")
                cursor.execute("ALTER TABLE orders ADD COLUMN deleted_at DATETIME")
                print("✓ Added deleted_at column")
            else:
                print("✓ deleted_at column already exists")
            
            conn.commit()
            print("\nMigration completed successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"Error during migration: {str(e)}")
            sys.exit(1)
        finally:
            conn.close()
    else:
        print("This migration script is for SQLite databases only.")
        print("For PostgreSQL, please use Alembic migrations or manually add the columns:")
        print("  ALTER TABLE orders ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;")
        print("  ALTER TABLE orders ADD COLUMN deleted_at TIMESTAMP;")

if __name__ == "__main__":
    migrate_database()
