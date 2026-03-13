#!/usr/bin/env python3
"""
Test the three new fixes for complex query issues:
1. Non-existent columns (student_name → first_name, last_name)
2. WHERE referencing wrong table (T2.gpa → T1.gpa)
3. Unnecessary JOINs removal
"""

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
- students.email
- students.enrollment_date
- students.department_id (FK to departments.department_id)
- enrollments.enrollment_id (PK)
- enrollments.student_id (FK to students.student_id)
- enrollments.course_id
- enrollments.enrollment_date
"""

FK = [
    ("students", "department_id", "departments", "department_id"),
    ("enrollments", "student_id", "students", "student_id"),
]

corrector = SQLPatternCorrector()

question = "show student names with GPA above 3.5"
sql = "SELECT T1.student_name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T2.gpa > 3.5"

print("="*70)
print("TEST: Fix Complex Query Issues")
print("="*70)
print(f"\nQuestion: {question}")
print(f"Original SQL: {sql}\n")

corrected = corrector.correct_sql(sql, question, SCHEMA_TEXT, FK)

print(f"Corrected SQL: {corrected}")
print("="*70)

# Check all fixes
print("\n📊 Validation:")
check1 = 'student_name' not in corrected.lower()
print(f"  1. No 'student_name' (non-existent): {'✅' if check1 else '❌'}")

check2 = 'first_name' in corrected or 'last_name' in corrected
print(f"  2. Has 'first_name' or 'last_name': {'✅' if check2 else '❌'}")

check3 = 'JOIN' not in corrected.upper()
print(f"  3. No unnecessary JOIN: {'✅' if check3 else '❌'}")

check4 = 'gpa > 3.5' in corrected or 'gpa>3.5' in corrected.replace(' ', '')
print(f"  4. WHERE has 'gpa > 3.5': {'✅' if check4 else '❌'}")

check5 = 'T2' not in corrected and 'enrollments' not in corrected
print(f"  5. No T2 or enrollments reference: {'✅' if check5 else '❌'}")

expected = "SELECT first_name, last_name FROM students WHERE gpa > 3.5"
print(f"\n✨ Expected: {expected}")

all_passed = check1 and check2 and check3 and check4 and check5
print(f"\n{'🎉 ALL TESTS PASSED!' if all_passed else '❌ SOME TESTS FAILED'}")
