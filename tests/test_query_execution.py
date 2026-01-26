"""
Test Query Execution Feature

This script tests the new query execution functionality
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_execution():
    """Test query execution with the datamind_test database"""
    
    print("🧪 Testing Query Execution Feature\n")
    print("=" * 60)
    
    # Test data
    schema = {
        "users": ["id", "username", "email", "created_at"],
        "products": ["id", "name", "price", "stock"],
    }
    
    test_queries = [
        "Show all users",
        "List top 3 expensive products",
        "Count total users",
    ]
    
    for i, question in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: '{question}'")
        print("-" * 60)
        
        # Request with execution
        request_data = {
            "question": question,
            "schema": schema,
            "use_sanitizer": True,
            "execute_query": False,  # Set to True when you have database_id
            "database_id": None  # Replace with actual database ID
        }
        
        try:
            response = requests.post(
                f"{API_URL}/query/nl2sql",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SQL Generated: {result['sql']}")
                
                if result.get('execution_result'):
                    exec_result = result['execution_result']
                    if exec_result['success']:
                        print(f"✅ Executed Successfully")
                        print(f"   Rows: {exec_result['row_count']}")
                        print(f"   Columns: {', '.join(exec_result['columns'])}")
                        if exec_result['is_visualizable']:
                            print(f"   📊 Visualizable: {exec_result['suggested_chart']}")
                    else:
                        print(f"❌ Execution Failed: {exec_result['error']}")
            else:
                print(f"❌ Request Failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("\n✨ Test Instructions:")
    print("1. Login to http://localhost:3000")
    print("2. Add a database connection (use datamind_test)")
    print("3. Go to Query tab")
    print("4. Check 'Execute query and show results'")
    print("5. Try the example queries")
    print("\nThe UI will display:")
    print("  - Generated SQL (always visible)")
    print("  - Execution results in a table")
    print("  - Bar chart visualization (for suitable queries)")
    print("  - Error messages (if query fails)")

if __name__ == "__main__":
    test_execution()
