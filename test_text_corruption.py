#!/usr/bin/env python3
"""
Test fix for text corruption in SQL generation
Example: "W JOIN ... HERE" should be "JOIN ... WHERE"
"""

import sys
import re
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

SCHEMA_TEXT = """
SCHEMA FOR student_db:
- courses.course_id (PK)
- courses.course_code
- courses.course_name
- courses.department_id (FK to departments.department_id)
- departments.department_id (PK)
- departments.department_name
"""

def test_text_corruption():
    """Test: Fix W JOIN and HERE corruption"""
    question = "Show all courses offered by the Mathematics department"
    corrupted_sql = "SELECT course_code FROM courses W JOIN departments ON courses.department_id = departments.department_idHERE departments.department_name = 'Mathematics'"
    
    print(f"Question: {question}")
    print(f"Corrupted SQL: {corrupted_sql}")
    print()
    
    foreign_keys = [
        ("courses", "department_id", "departments", "department_id"),
    ]
    
    corrector = SQLPatternCorrector()
    corrected = corrector.correct_sql(corrupted_sql, question, SCHEMA_TEXT, foreign_keys)
    
    print(f"Corrected SQL: {corrected}")
    print()
    
    # Check expectations
    # Verify corruption is fixed: no standalone HERE, no idHERE (only WHERE is allowed)
    has_standalone_here = bool(re.search(r'\bHERE\b(?!\s|$)', corrected, re.IGNORECASE))  # HERE as word
    # Check for HERE that's not part of WHERE: any char except W + HERE
    has_corrupted_concat = bool(re.search(r'[a-vx-z]HERE\b', corrected, re.IGNORECASE))  # excludes W
    
    checks = [
        ('W JOIN' not in corrected, "Should NOT have 'W JOIN'"),
        ('JOIN departments' in corrected, "Should have proper 'JOIN departments'"),
        (not has_standalone_here and not has_corrupted_concat, 
         f"Should NOT have corrupted 'HERE' (standalone={has_standalone_here}, concat like 'idHERE'={has_corrupted_concat})"),
        ('WHERE' in corrected, "Should have proper 'WHERE'"),
        ("department_name = 'Mathematics'" in corrected, "Should preserve the filter condition")
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
    print("Testing: Text Corruption Fix (W JOIN, HERE)")
    print("=" * 80)
    print()
    
    passed = test_text_corruption()
    
    print()
    if passed:
        print("🎉 Test passed! Text corruption fixed")
    else:
        print("❌ Test failed - corruption not fixed")
    
    sys.exit(0 if passed else 1)
