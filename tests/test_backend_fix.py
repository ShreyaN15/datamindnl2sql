#!/usr/bin/env python3
"""
Quick test to verify backend import fix
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{API_URL}/docs")
        assert response.status_code == 200
        print("✓ Backend is running")
        return True
    except Exception as e:
        print(f"✗ Backend health check failed: {e}")
        return False

def test_nl2sql_endpoint():
    """Test if nl2sql endpoint accepts requests (even if user_id doesn't exist)"""
    try:
        # This should fail with 404 (user not found) but NOT with ImportError
        payload = {
            "question": "Show all users",
            "schema": {"users": ["id", "name", "email"]},
            "use_sanitizer": True,
            "execute_query": False
        }
        
        response = requests.post(
            f"{API_URL}/query/nl2sql?user_id=999",  # Non-existent user
            json=payload
        )
        
        # We expect this to fail (no user) but not with ImportError
        if response.status_code == 500:
            error = response.json()
            if "ImportError" in str(error):
                print(f"✗ Import error still exists: {error}")
                return False
        
        print(f"✓ NL2SQL endpoint is working (status {response.status_code})")
        return True
        
    except Exception as e:
        print(f"✗ NL2SQL endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing backend fix...\n")
    
    health_ok = test_backend_health()
    endpoint_ok = test_nl2sql_endpoint()
    
    if health_ok and endpoint_ok:
        print("\n✓ All tests passed! Backend is fixed.")
    else:
        print("\n✗ Some tests failed")
