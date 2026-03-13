#!/usr/bin/env python3
"""
Test fix for "List all students in the Computer Science department"
Currently generates: SELECT students FROM departments WHERE department_name = 'Computer Science'
Expected: SELECT s.* FROM students s JOIN departments d ON ... WHERE d.department_name = 'Computer Science'
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

# Student DB schema
SCHEMA_TEXT = """
SCHEMA FOR student_db:
- students.student_id (PK)
- students.first_name
- students.last_name
- students.email
- students.department_id (FK to departments.department_id)
- departments.department_id (PK)
- departments.department_name
- departments.building
"""

def test_cs_students():
    """Test: List all students in the Computer Science department"""
    question = "List all students in the Computer Science department"
    wrong_sql = "SELECT students FROM departments WHERE department_name = 'Computer Science'"
    
    print(f"Question: {question}")
    print(f"Wrong SQL: {wrong_sql}")
    print()
    
    # Define foreign keys as tuples
    foreign_keys = [
        ("students", "department_id", "departments", "department_id"),
    ]
    
    corrector = SQLPatternCorrector()
    corrected = corrector.correct_sql(wrong_sql, question, SCHEMA_TEXT, foreign_keys)
    
    print(f"Corrected SQL: {corrected}")
    print()
    
    # Check expectations
    checks = [
        ('FROM students' in corrected, "Should query FROM students table"),
        ('JOIN departments' in corrected, "Should JOIN departments"),
        ('department_name' in corrected, "Should filter by department_name"),
        ("'Computer Science'" in corrected, "Should preserve the department name filter"),
        ('SELECT students FROM' not in corrected, "Should NOT select table name as column")
    ]
    
    all_passed = True
    for passed, description in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {description}")
        if not passed:
            all_passed = False
    
    return all_passed

if __name__ == '__main__':
    print("=" * 80)
    print("Testing: Students in CS Department Query Fix")
    print("=" * 80)
    print()
    
    passed = test_cs_students()
    
    print()
    if passed:
        print("🎉 Test passed! Query correctly rebuilt")
    else:
        print("❌ Test failed - query not properly fixed")
    
    sys.exit(0 if passed else 1)
