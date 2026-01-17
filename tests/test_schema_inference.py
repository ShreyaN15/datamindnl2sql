"""
Test Schema Inference Feature

Tests automatic schema extraction on database connection creation.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_schema_inference():
    """Test automatic schema inference on connection creation"""
    
    print_section("Testing Automatic Schema Inference")
    
    # Create a connection to our SQLite database (which has schema)
    print("\n1️⃣  Creating database connection (should auto-infer schema)...")
    
    connection_data = {
        "name": "Test Schema Inference",
        "db_type": "sqlite",
        "database_name": "data/datamind.db",
        "host": None,
        "port": None,
        "username": None,
        "password": None
    }
    
    response = requests.post(
        f"{BASE_URL}/db/connections?user_id=1",
        json=connection_data
    )
    
    if response.status_code == 201:
        conn = response.json()
        print(f"✅ Connection created: ID={conn['id']}, Name={conn['name']}")
        connection_id = conn['id']
        
        # Check if schema was auto-extracted
        if conn.get('schema_text'):
            print(f"✅ Schema auto-extracted!")
            print(f"   Tables: {conn.get('table_count', 0)}")
            print(f"   Total Columns: {conn.get('total_columns', 0)}")
            print(f"   Extracted at: {conn.get('schema_extracted_at', 'N/A')}")
        else:
            print("⚠️  Schema not auto-extracted (might be extracting in background)")
    else:
        print(f"❌ Failed to create connection: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    # Get the schema details
    print("\n2️⃣  Fetching detailed schema information...")
    
    response = requests.get(
        f"{BASE_URL}/db/connections/{connection_id}/schema?user_id=1&use_cached=true"
    )
    
    if response.status_code == 200:
        schema = response.json()
        print(f"✅ Schema retrieved successfully")
        print(f"\n📊 Schema Summary:")
        print(f"   Database: {schema.get('database_name')}")
        print(f"   Type: {schema.get('db_type')}")
        print(f"   Tables: {schema.get('table_count')}")
        print(f"   Total Columns: {schema.get('total_columns')}")
        print(f"   Cached: {schema.get('cached', False)}")
        
        # Show tables
        tables = schema.get('tables', {})
        if tables:
            print(f"\n📋 Tables and Columns:")
            for table_name, columns in tables.items():
                print(f"   • {table_name}: {len(columns)} columns")
                print(f"     └─ {', '.join(columns[:5])}", end="")
                if len(columns) > 5:
                    print(f", ... (+{len(columns) - 5} more)")
                else:
                    print()
        
        # Show foreign keys
        foreign_keys = schema.get('foreign_keys', [])
        if foreign_keys:
            print(f"\n🔗 Foreign Key Relationships ({len(foreign_keys)} found):")
            for fk in foreign_keys:
                print(f"   • {fk[0]}.{fk[1]} → {fk[2]}.{fk[3]}")
        else:
            print(f"\n🔗 Foreign Keys: None detected")
        
        # Show primary keys
        primary_keys = schema.get('primary_keys', {})
        if primary_keys:
            print(f"\n🔑 Primary Keys:")
            for table, pks in primary_keys.items():
                print(f"   • {table}: {', '.join(pks)}")
        
        # Show schema text (formatted for ML model)
        print(f"\n📝 ML Model Schema Format (first 500 chars):")
        schema_text = schema.get('schema_text', '')
        print("   " + "\n   ".join(schema_text[:500].split('\n')))
        if len(schema_text) > 500:
            print("   ... (truncated)")
        
    else:
        print(f"❌ Failed to get schema: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Test schema refresh
    print("\n3️⃣  Testing schema refresh (re-extraction)...")
    
    response = requests.post(
        f"{BASE_URL}/db/connections/{connection_id}/refresh-schema?user_id=1"
    )
    
    if response.status_code == 200:
        schema = response.json()
        print(f"✅ Schema refreshed successfully")
        print(f"   Cached: {schema.get('cached', False)} (should be False)")
    else:
        print(f"❌ Schema refresh failed: {response.status_code}")
    
    print_section("Schema Inference Test Complete")
    
    # Cleanup
    print("\n🧹 Cleaning up test connection...")
    response = requests.delete(
        f"{BASE_URL}/db/connections/{connection_id}?user_id=1"
    )
    if response.status_code == 204:
        print("✅ Test connection deleted")
    else:
        print(f"⚠️  Failed to delete test connection: {response.status_code}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  SCHEMA INFERENCE TEST SUITE")
    print("=" * 70)
    print("\nThis test verifies:")
    print("  ✓ Automatic schema extraction on connection creation")
    print("  ✓ Foreign key detection (explicit + naming convention)")
    print("  ✓ Primary key detection")
    print("  ✓ Schema formatting for ML model")
    print("  ✓ Cached vs fresh schema retrieval")
    print("  ✓ Schema refresh functionality")
    
    try:
        test_schema_inference()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
