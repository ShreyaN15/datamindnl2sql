#!/usr/bin/env python3
"""Test: List student names in Computer Science department"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

SCHEMA_TEXT = """
SCHEMA FOR student_db:
- students.student_id (PK)
- students.first_name
- students.last_name
- students.department_id (FK to departments.department_id)
- departments.department_id (PK)
- departments.department_name
"""

FK = [
    ("students", "department_id", "departments", "department_id"),
]

corrector = SQLPatternCorrector()

question = "List student names in Computer Science department"
sql = "SELECT first_name, last_name FROM students WHERE department_id = 'Computer Science'"

print("="*70)
print(f"Question: {question}")
print(f"Generated SQL: {sql}")
print("="*70)

corrected = corrector.correct_sql(sql, question, SCHEMA_TEXT, FK)

print(f"\nCorrected SQL: {corrected}")
print("="*70)

print("\n📊 Analysis:")
print(f"  1. Has JOIN to departments: {'✅' if 'JOIN departments' in corrected else '❌'}")
print(f"  2. WHERE uses department_name (not department_id): {'✅' if 'department_name' in corrected and 'WHERE department_id' not in corrected else '❌'}")
bad_pattern = "department_id = 'Computer Science'"
print(f"  3. No FK compared to string: {'✅' if bad_pattern not in corrected else '❌'}")

expected = "SELECT first_name, last_name FROM students JOIN departments ON students.department_id = departments.department_id WHERE departments.department_name = 'Computer Science'"
print(f"\n✨ Expected: {expected}")
