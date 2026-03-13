#!/usr/bin/env python3
"""Test: List students in Computer Science department"""

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

question = "List students in Computer Science department"
sql = "SELECT student_id FROM departments WHERE department_name = 'Computer Science'"

print("="*70)
print(f"Question: {question}")
print(f"Generated SQL: {sql}")
print("="*70)

corrected = corrector.correct_sql(sql, question, SCHEMA_TEXT, FK)

print(f"\nCorrected SQL: {corrected}")
print("="*70)

# Expected: Should select from students with JOIN to departments
print("\n📊 Analysis:")
print(f"  1. FROM students (not departments): {'✅' if 'FROM students' in corrected else '❌'}")
print(f"  2. Has JOIN to departments: {'✅' if 'JOIN departments' in corrected else '❌'}")
print(f"  3. WHERE has department_name condition: {'✅' if 'department_name' in corrected else '❌'}")

expected = "SELECT student_id FROM students JOIN departments ON students.department_id = departments.department_id WHERE department_name = 'Computer Science'"
print(f"\n✨ Expected (minimal): SELECT student_id FROM students JOIN departments ... WHERE department_name = 'Computer Science'")
print(f"   Has key parts: {'✅' if all(x in corrected for x in ['FROM students', 'JOIN departments', 'department_name']) else '❌'}")
