#!/usr/bin/env python3
"""
Migration script to add priority column to needs table
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add parent directory to path to import database module
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import DATABASE_URL


def migrate():
    """Add priority column to needs table with default value of 1.0"""
    
    # Extract database path from DATABASE_URL
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
    else:
        print(f"Unsupported database type: {DATABASE_URL}")
        return False
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if priority column already exists
        cursor.execute("PRAGMA table_info(needs)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'priority' in column_names:
            print("Priority column already exists in needs table")
            return True
        
        # Add priority column with default value
        cursor.execute("ALTER TABLE needs ADD COLUMN priority REAL DEFAULT 1.0")
        
        # Update existing records to have priority = 1.0
        cursor.execute("UPDATE needs SET priority = 1.0 WHERE priority IS NULL")
        
        # Commit changes
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(needs)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'priority' in column_names:
            print("Successfully added priority column to needs table")
            
            # Count affected rows
            cursor.execute("SELECT COUNT(*) FROM needs")
            count = cursor.fetchone()[0]
            print(f"Updated {count} existing needs with default priority of 1.0")
            
            return True
        else:
            print("Failed to add priority column")
            return False
            
    except Exception as e:
        print(f"Migration error: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)