"""
Test script for authentication and database connection management

This script tests the user authentication and database connection endpoints.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_user_registration():
    """Test user registration"""
    print_section("TEST 1: User Registration")
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        user = response.json()
        print(f"✅ User registered successfully!")
        print(f"User ID: {user['id']}")
        print(f"Username: {user['username']}")
        print(f"Email: {user['email']}")
        return user['id']
    else:
        print(f"❌ Registration failed: {response.json()}")
        return None

def test_user_login(username, password):
    """Test user login"""
    print_section("TEST 2: User Login")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": username,
            "password": password
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Login successful!")
        print(f"User ID: {result['user']['id']}")
        print(f"Message: {result['message']}")
        return result['user']['id']
    else:
        print(f"❌ Login failed: {response.json()}")
        return None

def test_create_database_connection(user_id):
    """Test creating a database connection"""
    print_section("TEST 3: Create Database Connection")
    
    response = requests.post(
        f"{BASE_URL}/db/connections?user_id={user_id}",
        json={
            "name": "Test MySQL Connection",
            "db_type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database_name": "test_db",
            "username": "root",
            "password": "password"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        conn = response.json()
        print(f"✅ Connection created successfully!")
        print(f"Connection ID: {conn['id']}")
        print(f"Name: {conn['name']}")
        print(f"Type: {conn['db_type']}")
        return conn['id']
    else:
        print(f"❌ Connection creation failed: {response.json()}")
        return None

def test_list_connections(user_id):
    """Test listing database connections"""
    print_section("TEST 4: List Database Connections")
    
    response = requests.get(f"{BASE_URL}/db/connections?user_id={user_id}")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Connections retrieved successfully!")
        print(f"Total connections: {result['total']}")
        for conn in result['connections']:
            print(f"  - {conn['name']} ({conn['db_type']})")
    else:
        print(f"❌ Failed to list connections: {response.json()}")

def test_get_connection(connection_id, user_id):
    """Test getting a specific connection"""
    print_section("TEST 5: Get Specific Connection")
    
    response = requests.get(
        f"{BASE_URL}/db/connections/{connection_id}?user_id={user_id}"
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        conn = response.json()
        print(f"✅ Connection retrieved successfully!")
        print(f"ID: {conn['id']}")
        print(f"Name: {conn['name']}")
        print(f"Type: {conn['db_type']}")
        print(f"Database: {conn['database_name']}")
        print(f"Status: {conn['last_test_status']}")
    else:
        print(f"❌ Failed to get connection: {response.json()}")

def test_update_connection(connection_id, user_id):
    """Test updating a connection"""
    print_section("TEST 6: Update Connection")
    
    response = requests.put(
        f"{BASE_URL}/db/connections/{connection_id}?user_id={user_id}",
        json={
            "name": "Updated MySQL Connection",
            "is_active": True
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        conn = response.json()
        print(f"✅ Connection updated successfully!")
        print(f"New name: {conn['name']}")
    else:
        print(f"❌ Failed to update connection: {response.json()}")

def test_create_sqlite_connection(user_id):
    """Test creating a SQLite connection"""
    print_section("TEST 7: Create SQLite Connection")
    
    response = requests.post(
        f"{BASE_URL}/db/connections?user_id={user_id}",
        json={
            "name": "Local SQLite DB",
            "db_type": "sqlite",
            "database_name": "data/datamind.db"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        conn = response.json()
        print(f"✅ SQLite connection created successfully!")
        print(f"Connection ID: {conn['id']}")
        return conn['id']
    else:
        print(f"❌ SQLite connection creation failed: {response.json()}")
        return None

def test_connection_test(connection_id, user_id):
    """Test database connection testing"""
    print_section("TEST 8: Test Database Connection")
    
    response = requests.post(
        f"{BASE_URL}/db/connections/{connection_id}/test?user_id={user_id}"
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Connection test completed!")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        if result.get('details'):
            print(f"Details: {json.dumps(result['details'], indent=2)}")
    else:
        print(f"❌ Connection test failed: {response.json()}")

def test_get_schema(connection_id, user_id):
    """Test getting database schema"""
    print_section("TEST 9: Get Database Schema")
    
    response = requests.get(
        f"{BASE_URL}/db/connections/{connection_id}/schema?user_id={user_id}"
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Schema retrieved successfully!")
        print(f"Connection: {result['connection_name']}")
        print(f"Database: {result['database_name']}")
        schema = result['schema']
        print(f"Tables found: {len(schema['tables'])}")
        for table, columns in list(schema['tables'].items())[:3]:  # Show first 3 tables
            print(f"  Table: {table}")
            print(f"    Columns: {', '.join(columns[:5])}...")  # Show first 5 columns
    else:
        print(f"❌ Failed to get schema: {response.json()}")

if __name__ == "__main__":
    print("\n🚀 Starting Authentication and Database Connection Tests\n")
    
    try:
        # Test 1: Register user
        user_id = test_user_registration()
        if not user_id:
            # Try to login with existing user
            user_id = test_user_login("testuser", "password123")
        
        if not user_id:
            print("\n❌ Failed to get user ID. Cannot continue tests.")
            exit(1)
        
        # Test 2: Login
        test_user_login("testuser", "password123")
        
        # Test 3: Create database connection
        connection_id = test_create_database_connection(user_id)
        
        if connection_id:
            # Test 4: List connections
            test_list_connections(user_id)
            
            # Test 5: Get specific connection
            test_get_connection(connection_id, user_id)
            
            # Test 6: Update connection
            test_update_connection(connection_id, user_id)
        
        # Test 7: Create SQLite connection
        sqlite_conn_id = test_create_sqlite_connection(user_id)
        
        if sqlite_conn_id:
            # Test 8: Test the SQLite connection
            test_connection_test(sqlite_conn_id, user_id)
            
            # Test 9: Get schema from SQLite connection
            test_get_schema(sqlite_conn_id, user_id)
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED!")
        print("=" * 80)
        print("\nAPI Documentation: http://127.0.0.1:8000/docs")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
