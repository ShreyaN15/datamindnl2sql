"""
End-to-End NL2SQL Test with PostgreSQL

Tests the complete flow:
1. Get schema from PostgreSQL connection
2. Pass schema to ML model
3. Generate SQL from natural language
4. Validate SQL correctness
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_nl2sql_with_postgres():
    """Test NL2SQL with real PostgreSQL schema"""
    
    print_header("End-to-End NL2SQL Test with PostgreSQL")
    
    # Step 1: Get the PostgreSQL connection schema
    print("\n1️⃣  Fetching PostgreSQL schema...")
    
    connection_id = 3  # From previous test
    response = requests.get(
        f"{BASE_URL}/db/connections/{connection_id}/schema?user_id=1"
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get schema: {response.status_code}")
        return
    
    schema_data = response.json()
    schema_text = schema_data['schema_text']
    tables_dict = schema_data['tables']  # Already in dict format
    foreign_keys_raw = schema_data['foreign_keys']
    
    # Convert foreign keys to API format
    foreign_keys_api = []
    for fk in foreign_keys_raw:
        foreign_keys_api.append({
            "from_table": fk[0],
            "from_column": fk[1],
            "to_table": fk[2],
            "to_column": fk[3]
        })
    
    print(f"✅ Schema retrieved successfully!")
    print(f"   Tables: {schema_data['table_count']}")
    print(f"   Columns: {schema_data['total_columns']}")
    print(f"   Foreign Keys: {len(foreign_keys_raw)}")
    
    # Step 2: Test multiple natural language queries
    test_queries = [
        {
            "question": "Show all users",
            "expected_tables": ["users"],
            "expected_columns": ["*"],
        },
        {
            "question": "Get all products with their category names",
            "expected_tables": ["products", "categories"],
            "expected_join": True,
        },
        {
            "question": "Find all orders made by user with username john_doe",
            "expected_tables": ["orders", "users"],
            "expected_join": True,
        },
        {
            "question": "What are the top 5 most expensive products",
            "expected_tables": ["products"],
            "expected_order_by": True,
            "expected_limit": 5,
        },
        {
            "question": "Show total revenue from completed orders",
            "expected_tables": ["orders"],
            "expected_aggregate": "SUM",
            "expected_where": True,
        },
        {
            "question": "List all products that have reviews with rating 5",
            "expected_tables": ["products", "reviews"],
            "expected_join": True,
            "expected_where": True,
        },
        {
            "question": "Count how many orders each user has made",
            "expected_tables": ["orders", "users"],
            "expected_aggregate": "COUNT",
            "expected_group_by": True,
        },
        {
            "question": "Get product names and their average ratings",
            "expected_tables": ["products", "reviews"],
            "expected_aggregate": "AVG",
            "expected_group_by": True,
        },
    ]
    
    print(f"\n2️⃣  Testing {len(test_queries)} Natural Language Queries...")
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"Query #{i}: \"{test['question']}\"")
        print(f"{'─' * 80}")
        
        # Call NL2SQL API
        response = requests.post(
            f"{BASE_URL}/query/nl2sql",
            json={
                "question": test['question'],
                "schema": tables_dict,  # Use dict format
                "foreign_keys": foreign_keys_api,  # Use API format
                "use_sanitizer": True
            }
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"   {response.text}")
            results.append({
                "question": test['question'],
                "status": "API_ERROR",
                "sql": None
            })
            continue
        
        result = response.json()
        
        print(f"\n📝 Generated SQL:")
        print(f"   {result['sql']}")
        
        if result.get('was_corrected'):
            print(f"\n⚙️  SQL was corrected by sanitizer")
            print(f"   Original: {result.get('raw_sql', 'N/A')}")
            print(f"   Corrections: {result.get('errors', [])}")
        
        # Analyze the SQL
        sql = result['sql'].upper()
        analysis = {
            "question": test['question'],
            "sql": result['sql'],
            "status": "GENERATED",
            "checks": {}
        }
        
        # Check expected elements
        print(f"\n🔍 Validation:")
        
        # Check tables
        if 'expected_tables' in test:
            tables_found = all(table.upper() in sql for table in test['expected_tables'])
            analysis['checks']['tables'] = tables_found
            status = "✅" if tables_found else "⚠️ "
            print(f"   {status} Expected tables: {test['expected_tables']}")
        
        # Check JOIN
        if test.get('expected_join'):
            has_join = 'JOIN' in sql
            analysis['checks']['join'] = has_join
            status = "✅" if has_join else "⚠️ "
            print(f"   {status} Has JOIN: {has_join}")
        
        # Check WHERE
        if test.get('expected_where'):
            has_where = 'WHERE' in sql
            analysis['checks']['where'] = has_where
            status = "✅" if has_where else "⚠️ "
            print(f"   {status} Has WHERE clause: {has_where}")
        
        # Check ORDER BY
        if test.get('expected_order_by'):
            has_order = 'ORDER BY' in sql
            analysis['checks']['order_by'] = has_order
            status = "✅" if has_order else "⚠️ "
            print(f"   {status} Has ORDER BY: {has_order}")
        
        # Check LIMIT
        if test.get('expected_limit'):
            has_limit = 'LIMIT' in sql
            analysis['checks']['limit'] = has_limit
            status = "✅" if has_limit else "⚠️ "
            print(f"   {status} Has LIMIT: {has_limit}")
        
        # Check aggregates
        if test.get('expected_aggregate'):
            agg = test['expected_aggregate']
            has_agg = agg in sql
            analysis['checks']['aggregate'] = has_agg
            status = "✅" if has_agg else "⚠️ "
            print(f"   {status} Has {agg}: {has_agg}")
        
        # Check GROUP BY
        if test.get('expected_group_by'):
            has_group = 'GROUP BY' in sql
            analysis['checks']['group_by'] = has_group
            status = "✅" if has_group else "⚠️ "
            print(f"   {status} Has GROUP BY: {has_group}")
        
        # Overall validity
        all_checks_passed = all(analysis['checks'].values())
        analysis['all_passed'] = all_checks_passed
        
        if all_checks_passed:
            print(f"\n   ✅ SQL appears logically correct!")
            analysis['status'] = "VALID"
        else:
            print(f"\n   ⚠️  Some expected elements missing")
            analysis['status'] = "INCOMPLETE"
        
        results.append(analysis)
    
    # Summary
    print_header("Test Summary")
    
    total = len(results)
    valid = sum(1 for r in results if r['status'] == 'VALID')
    incomplete = sum(1 for r in results if r['status'] == 'INCOMPLETE')
    errors = sum(1 for r in results if r['status'] == 'API_ERROR')
    
    print(f"\n📊 Overall Results:")
    print(f"   Total Queries: {total}")
    print(f"   ✅ Valid SQL: {valid} ({valid/total*100:.1f}%)")
    print(f"   ⚠️  Incomplete: {incomplete} ({incomplete/total*100:.1f}%)")
    print(f"   ❌ Errors: {errors} ({errors/total*100:.1f}%)")
    
    # Show all generated SQLs
    print(f"\n📋 All Generated SQL Queries:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['question']}")
        print(f"   SQL: {r['sql']}")
        print(f"   Status: {r['status']}")
    
    print_header("Test Complete")
    
    return results


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  NL2SQL End-to-End Test")
    print("  Using PostgreSQL Schema with ML Model")
    print("=" * 80)
    print("\nThis test will:")
    print("  ✓ Fetch auto-extracted PostgreSQL schema")
    print("  ✓ Pass schema to T5 NL2SQL model")
    print("  ✓ Generate SQL for 8 different natural language queries")
    print("  ✓ Validate SQL correctness (tables, joins, filters, etc.)")
    print("  ✓ Apply SQL sanitizer for corrections")
    
    try:
        results = test_nl2sql_with_postgres()
        
        # Exit code based on results
        if results:
            valid_count = sum(1 for r in results if r['status'] == 'VALID')
            if valid_count >= len(results) * 0.75:  # 75% success rate
                print(f"\n✅ Test PASSED! {valid_count}/{len(results)} queries generated valid SQL")
                exit(0)
            else:
                print(f"\n⚠️  Test PARTIAL! Only {valid_count}/{len(results)} queries generated valid SQL")
                exit(1)
        else:
            print(f"\n❌ Test FAILED! No results generated")
            exit(2)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(3)
