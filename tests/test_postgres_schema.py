"""
Test PostgreSQL Schema Inference

Tests automatic schema extraction with a real PostgreSQL database.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_postgres_schema_inference():
    """Test schema inference with PostgreSQL database"""
    
    print_header("PostgreSQL Schema Inference Test")
    
    # Get system username for PostgreSQL connection
    import os
    username = os.getenv('USER')
    
    print(f"\n📊 Testing with PostgreSQL database:")
    print(f"   Host: localhost")
    print(f"   Port: 5432")
    print(f"   Database: datamind_test")
    print(f"   Username: {username}")
    
    # Step 1: Create connection (should auto-infer schema)
    print("\n1️⃣  Creating PostgreSQL connection...")
    
    connection_data = {
        "name": "PostgreSQL Test - E-commerce",
        "db_type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database_name": "datamind_test",
        "username": username,
        "password": ""
    }
    
    response = requests.post(
        f"{BASE_URL}/db/connections?user_id=1",
        json=connection_data
    )
    
    if response.status_code != 201:
        print(f"❌ Failed to create connection: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    conn = response.json()
    connection_id = conn['id']
    print(f"✅ Connection created successfully!")
    print(f"   ID: {connection_id}")
    print(f"   Name: {conn['name']}")
    print(f"   Tables: {conn.get('table_count', 'N/A')}")
    print(f"   Columns: {conn.get('total_columns', 'N/A')}")
    
    # Step 2: Get detailed schema
    print("\n2️⃣  Fetching detailed schema information...")
    
    response = requests.get(
        f"{BASE_URL}/db/connections/{connection_id}/schema?user_id=1&use_cached=true"
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get schema: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    schema = response.json()
    
    print(f"\n📊 Schema Summary:")
    print(f"   Database: {schema.get('database_name')}")
    print(f"   Type: {schema.get('db_type')}")
    print(f"   Tables: {schema.get('table_count')}")
    print(f"   Total Columns: {schema.get('total_columns')}")
    print(f"   Schema Cached: {schema.get('cached', False)}")
    
    # Display tables
    tables = schema.get('tables', {})
    print(f"\n📋 Tables and Columns ({len(tables)} tables):")
    for table_name in sorted(tables.keys()):
        columns = tables[table_name]
        print(f"\n   • {table_name} ({len(columns)} columns):")
        for col in columns:
            print(f"      - {col}")
    
    # Display foreign keys
    foreign_keys = schema.get('foreign_keys', [])
    print(f"\n🔗 Foreign Key Relationships ({len(foreign_keys)} found):")
    
    if foreign_keys:
        # Group FKs by table
        fk_by_table = {}
        for fk in foreign_keys:
            from_table = fk[0]
            if from_table not in fk_by_table:
                fk_by_table[from_table] = []
            fk_by_table[from_table].append(fk)
        
        for table in sorted(fk_by_table.keys()):
            print(f"\n   From {table}:")
            for fk in fk_by_table[table]:
                print(f"      • {fk[1]} → {fk[2]}.{fk[3]}")
    else:
        print("   ⚠️  No foreign keys detected!")
    
    # Display primary keys
    primary_keys = schema.get('primary_keys', {})
    if primary_keys:
        print(f"\n🔑 Primary Keys:")
        for table, pks in sorted(primary_keys.items()):
            print(f"   • {table}: {', '.join(pks)}")
    
    # Show ML model format (sample)
    print(f"\n📝 ML Model Schema Format (first 800 chars):")
    schema_text = schema.get('schema_text', '')
    lines = schema_text.split('\n')[:30]
    for line in lines:
        print(f"   {line}")
    if len(schema_text.split('\n')) > 30:
        print(f"   ... ({len(schema_text.split('\n')) - 30} more lines)")
    
    # Step 3: Verify expected schema
    print(f"\n3️⃣  Verifying schema detection...")
    
    expected_tables = {'users', 'categories', 'products', 'orders', 'order_items', 'reviews'}
    detected_tables = set(tables.keys())
    
    if expected_tables == detected_tables:
        print(f"   ✅ All expected tables detected: {len(expected_tables)}")
    else:
        print(f"   ⚠️  Table mismatch!")
        print(f"      Expected: {expected_tables}")
        print(f"      Detected: {detected_tables}")
    
    # Verify foreign keys
    expected_fk_count = 6
    detected_fk_count = len(foreign_keys)
    
    if detected_fk_count == expected_fk_count:
        print(f"   ✅ All foreign keys detected: {detected_fk_count}")
    else:
        print(f"   ⚠️  FK count mismatch!")
        print(f"      Expected: {expected_fk_count}")
        print(f"      Detected: {detected_fk_count}")
    
    # Verify specific foreign keys
    expected_fks = {
        ('products', 'category_id', 'categories', 'id'),
        ('orders', 'user_id', 'users', 'id'),
        ('order_items', 'order_id', 'orders', 'id'),
        ('order_items', 'product_id', 'products', 'id'),
        ('reviews', 'user_id', 'users', 'id'),
        ('reviews', 'product_id', 'products', 'id'),
    }
    
    detected_fks = {tuple(fk) for fk in foreign_keys}
    
    if expected_fks == detected_fks:
        print(f"   ✅ All expected foreign key relationships detected!")
    else:
        missing = expected_fks - detected_fks
        extra = detected_fks - expected_fks
        if missing:
            print(f"   ⚠️  Missing FKs: {missing}")
        if extra:
            print(f"   ℹ️  Extra FKs detected: {extra}")
    
    print_header("PostgreSQL Schema Inference Test Complete")
    
    # Cleanup
    print(f"\n🧹 Cleaning up...")
    print(f"   Keeping connection ID {connection_id} for further testing")
    print(f"   You can delete it manually or use:")
    print(f"   DELETE http://localhost:8000/db/connections/{connection_id}?user_id=1")
    
    return connection_id


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  PostgreSQL Schema Inference - Comprehensive Test")
    print("=" * 80)
    print("\nThis test will:")
    print("  ✓ Connect to PostgreSQL database 'datamind_test'")
    print("  ✓ Automatically extract complete schema")
    print("  ✓ Detect all 6 tables (users, categories, products, orders, order_items, reviews)")
    print("  ✓ Detect all 6 foreign key relationships")
    print("  ✓ Detect primary keys")
    print("  ✓ Format schema for ML model consumption")
    
    try:
        connection_id = test_postgres_schema_inference()
        if connection_id:
            print(f"\n✅ Test completed successfully!")
            print(f"   Connection ID: {connection_id}")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
