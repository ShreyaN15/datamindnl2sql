#!/usr/bin/env python3
"""Comprehensive tests for the three new fixes"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

SCHEMA_TEXT = """
SCHEMA FOR student_db:
- students.student_id (PK)
- students.first_name
- students.last_name
- students.age
- students.gpa
- departments.department_id (PK)
- departments.department_name
- enrollments.enrollment_id (PK)
- enrollments.student_id (FK)
- enrollments.course_id
"""

FK = [
    ("students", "department_id", "departments", "department_id"),
    ("enrollments", "student_id", "students", "student_id"),
]

corrector = SQLPatternCorrector()

tests = [
    {
        "name": "Original issue - student_name + wrong table + unnecessary JOIN",
        "question": "show student names with GPA above 3.5",
        "sql": "SELECT T1.student_name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T2.gpa > 3.5",
        "should_have": ["first_name", "last_name", "WHERE gpa"],
        "should_not_have": ["student_name", "T2", "enrollments", "JOIN"]
    },
    {
        "name": "Necessary JOIN should be preserved",
        "question": "students with their department names",
        "sql": "SELECT first_name, last_name, department_name FROM students JOIN departments ON students.department_id = departments.department_id",
        "should_have": ["JOIN departments", "department_name"],
        "should_not_have": []
    },
    {
        "name": "professor_name should also be fixed",
        "question": "show professor names",
        "sql": "SELECT professor_name FROM professors",
        "should_have": ["first_name", "last_name"],
        "should_not_have": ["professor_name"]
    }
]

print("="*70)
print("COMPREHENSIVE TESTS FOR NEW FIXES")
print("="*70)

passed = 0
failed = 0

for i, test in enumerate(tests, 1):
    print(f"\n{'='*70}")
    print(f"Test {i}: {test['name']}")
    print(f"{'='*70}")
    print(f"Question: {test['question']}")
    print(f"Original: {test['sql']}")
    
    corrected = corrector.correct_sql(test['sql'], test['question'], SCHEMA_TEXT, FK)
    print(f"Corrected: {corrected}")
    
    # Check assertions
    test_passed = True
    for phrase in test['should_have']:
        if phrase.lower() not in corrected.lower():
            print(f"  ❌ Missing: '{phrase}'")
            test_passed = False
    
    for phrase in test['should_not_have']:
        if phrase.lower() in corrected.lower():
            print(f"  ❌ Should not have: '{phrase}'")
            test_passed = False
    
    if test_passed:
        print(f"  ✅ PASSED")
        passed += 1
    else:
        failed += 1

print(f"\n{'='*70}")
print(f"RESULTS: {passed}/{len(tests)} tests passed")
if failed == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print(f"❌ {failed} test(s) failed")
print(f"{'='*70}")
