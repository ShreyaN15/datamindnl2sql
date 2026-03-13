#!/usr/bin/env python3
"""
Test case for: Show grades of John Smith
Generated SQL: SELECT grade_id FROM grades WHERE department_id = 'John Smith'

Issue: Person name in department_id column (FK), should filter by student name
Expected: grades -> students with student name filter
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

# Test data
question = "Show grades of John Smith"
sql = "SELECT grade_id FROM grades WHERE department_id = 'John Smith'"

schema_text = """
students: student_id, first_name, last_name, email, date_of_birth, gpa, department_id
grades: grade_id, student_id, course_id, grade, semester
courses: course_id, course_name, course_code, credits, professor_id
professors: professor_id, first_name, last_name, email, hire_date, department_id
departments: department_id, department_name
"""

foreign_keys = [
    ("students", "department_id", "departments", "department_id"),
    ("grades", "student_id", "students", "student_id"),
    ("grades", "course_id", "courses", "course_id"),
    ("courses", "professor_id", "professors", "professor_id"),
    ("professors", "department_id", "departments", "department_id"),
]

print("=" * 70)
print(f"Question: {question}")
print(f"Generated SQL: {sql}")
print("=" * 70)
print()

# Apply pattern corrector
corrector = SQLPatternCorrector()
corrected = corrector.correct_sql(sql, question, schema_text, foreign_keys)

print(f"Corrected SQL: {corrected}")
print("=" * 70)
print()

# Analyze the correction
print("📊 Analysis:")
if 'students' in corrected.lower():
    print("  1. References students table: ✅")
else:
    print("  1. References students table: ❌")

if 'grades' in corrected.lower():
    print("  2. References grades table: ✅")
else:
    print("  2. References grades table: ❌")

if 'first_name' in corrected.lower() and 'last_name' in corrected.lower():
    print("  3. Filters by first_name and last_name: ✅")
else:
    print("  3. Filters by first_name and last_name: ❌")

if 'department_id' not in corrected.split('WHERE')[1] if 'WHERE' in corrected else True:
    print("  4. No longer uses department_id in WHERE: ✅")
else:
    print("  4. No longer uses department_id in WHERE: ❌")

if "first_name = 'John'" in corrected and "last_name = 'Smith'" in corrected:
    print("  5. Correctly parses 'John Smith' to separate names: ✅")
else:
    print("  5. Correctly parses 'John Smith' to separate names: ❌")

print()
if all([
    'students' in corrected.lower(),
    'grades' in corrected.lower(),
    'first_name' in corrected.lower(),
    'last_name' in corrected.lower(),
    'department_id' not in corrected.split('WHERE')[1] if 'WHERE' in corrected else True
]):
    print("✅ FIXED: Query properly filters grades by student name")
else:
    print("❌ ISSUE: Fix #7 should detect person name in FK column and rebuild query")
    print()
    print("Expected: SELECT g.* FROM students s JOIN grades g ON s.student_id = g.student_id")
    print("          WHERE s.first_name = 'John' AND s.last_name = 'Smith'")
