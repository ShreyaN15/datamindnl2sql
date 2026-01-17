"""
Database Schema Migration Script

Adds schema inference columns to the database_connections table.
Run this script to update existing database to support schema storage.
"""

import sqlite3
from pathlib import Path


def migrate_database(db_path: str = "data/datamind.db"):
    """
    Add schema-related columns to database_connections table.
    
    New columns:
    - schema_text: Formatted schema for ML model
    - schema_tables: JSON of tables and columns
    - foreign_keys: JSON of FK relationships
    - primary_keys: JSON of primary keys
    - column_types: JSON of column data types
    - table_count: Number of tables
    - total_columns: Total columns
    - schema_extracted_at: Timestamp of last extraction
    """
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"❌ Database not found at: {db_path}")
        print("   Please create the database first by running the application.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(database_connections)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        new_columns = {
            'schema_text': 'TEXT',
            'schema_tables': 'TEXT',
            'foreign_keys': 'TEXT',
            'primary_keys': 'TEXT',
            'column_types': 'TEXT',
            'table_count': 'INTEGER',
            'total_columns': 'INTEGER',
            'schema_extracted_at': 'TIMESTAMP'
        }
        
        # Add missing columns
        added_count = 0
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                print(f"➕ Adding column: {col_name} ({col_type})")
                cursor.execute(f"ALTER TABLE database_connections ADD COLUMN {col_name} {col_type}")
                added_count += 1
            else:
                print(f"✓ Column already exists: {col_name}")
        
        conn.commit()
        
        if added_count > 0:
            print(f"\n✅ Migration successful! Added {added_count} new columns.")
        else:
            print(f"\n✅ Database already up to date!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Database Schema Migration")
    print("=" * 60)
    print()
    
    success = migrate_database()
    
    print()
    print("=" * 60)
    
    if success:
        print("Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Restart your application server")
        print("2. Create a new database connection to test schema inference")
        print("3. Check logs for schema extraction details")
    else:
        print("Migration failed. Please check the error message above.")
    
    print("=" * 60)
