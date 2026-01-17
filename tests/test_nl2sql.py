"""
Test script for NL2SQL endpoint

This script tests the NL2SQL service locally before running the full API.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.engines.ml.nl2sql_service import NL2SQLService
from app.utils.schema_builder import build_schema_from_dict


def test_basic_query():
    """Test basic SQL generation"""
    print("=" * 80)
    print("TEST 1: Basic SQL Generation")
    print("=" * 80)
    
    # Initialize service
    service = NL2SQLService()
    service.load_model()
    
    # Define schema
    schema_dict = {
        "users": ["id", "name", "email", "country"],
        "orders": ["id", "user_id", "total", "created_at"]
    }
    
    foreign_keys = [
        ("orders", "user_id", "users", "id")
    ]
    
    # Test questions
    questions = [
        "How many users are from USA?",
        "List all user names",
        "What is the total amount of all orders?",
        "Show users who have placed orders"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        sql = service.generate_from_dict(
            question=question,
            tables_dict=schema_dict,
            foreign_keys=foreign_keys,
            use_sanitizer=True
        )
        print(f"SQL: {sql}")
    
    print("\n" + "=" * 80)


def test_detailed_response():
    """Test detailed response with validation info"""
    print("\n" + "=" * 80)
    print("TEST 2: Detailed Response with Validation")
    print("=" * 80)
    
    service = NL2SQLService()
    service.load_model()
    
    schema_dict = {
        "customers": ["customer_id", "name", "email", "country"],
        "products": ["product_id", "name", "price"]
    }
    
    schema_text, fks = build_schema_from_dict(schema_dict)
    
    question = "How many customers are from Canada?"
    
    result = service.generate_sql_with_details(
        question=question,
        schema_text=schema_text,
        foreign_keys=fks,
        use_sanitizer=True
    )
    
    print(f"\nQuestion: {result['question']}")
    print(f"Raw SQL: {result['raw_sql']}")
    print(f"Corrected SQL: {result['corrected_sql']}")
    print(f"Is Valid: {result['is_valid']}")
    print(f"Was Corrected: {result['was_corrected']}")
    if result['errors']:
        print(f"Errors/Corrections: {result['errors']}")
    
    print("\n" + "=" * 80)


def test_without_sanitizer():
    """Test without SQL sanitizer"""
    print("\n" + "=" * 80)
    print("TEST 3: Generation Without Sanitizer")
    print("=" * 80)
    
    service = NL2SQLService()
    service.load_model()
    
    schema_dict = {
        "employees": ["id", "name", "department", "salary"],
    }
    
    schema_text, _ = build_schema_from_dict(schema_dict)
    
    question = "What is the average salary of employees?"
    
    print(f"\nQuestion: {question}")
    
    # With sanitizer
    sql_with = service.generate_sql(
        question=question,
        schema_text=schema_text,
        use_sanitizer=True
    )
    print(f"With Sanitizer: {sql_with}")
    
    # Without sanitizer
    sql_without = service.generate_sql(
        question=question,
        schema_text=schema_text,
        use_sanitizer=False
    )
    print(f"Without Sanitizer: {sql_without}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting NL2SQL Service Tests\n")
    
    try:
        test_basic_query()
        test_detailed_response()
        test_without_sanitizer()
        
        print("\n✅ All tests completed successfully!\n")
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
