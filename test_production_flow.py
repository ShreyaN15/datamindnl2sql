#!/usr/bin/env python3
"""
Test the EXACT flow that happens in production:
1. Sanitizer generates SQL with corruption
2. Pattern corrector fixes it
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

corrector = SQLPatternCorrector()

# This is what the SANITIZER generates (from the logs):
# "SELECT COUNT(*), departments.department_name FROM students GROUP BY"
# Then pattern corrector injects JOIN, creating corruption

sql = "SELECT COUNT(*), departments.department_name FROM students GROUP BY"
question = "Count of students grouped by department"

schema_text = """
students: student_id, first_name, last_name, email, date_of_birth, enrollment_date, major, gpa, year_level, department_id
departments: department_id, department_name, building, budget, chair_professor_id
enrollments: enrollment_id, student_id, course_id, enrollment_date, grade, status
courses: course_id, course_name, course_code, credits, semester, professor_id, department_id
professors: professor_id, first_name, last_name, email, hire_date, salary, department_id
grades: grade_id, enrollment_id, assignment_name, assignment_type, max_score, achieved_score, weight, graded_date
"""

foreign_keys = [
    ('students', 'department_id', 'departments', 'department_id'),
    ('enrollments', 'student_id', 'students', 'student_id'),
    ('enrollments', 'course_id', 'courses', 'course_id'),
    ('courses', 'professor_id', 'professors', 'professor_id'),
    ('courses', 'department_id', 'departments', 'department_id'),
    ('professors', 'department_id', 'departments', 'department_id'),
    ('grades', 'enrollment_id', 'enrollments', 'enrollment_id'),
]

print("="*70)
print("Simulating PRODUCTION FLOW")
print("="*70)
print(f"Sanitizer output: {sql}")
print()

corrected = corrector.correct_sql(sql, question, schema_text, foreign_keys)

print(f"Pattern corrector output: {corrected}")
print("="*70)
print()

# Analysis
import re

has_syntax_error = bool(re.search(r'[a-fh-z0-9_]ROUP\s+BY|students\s+G\s+JOIN|GROUP\s+BY\s+GROUP\s+BY', corrected, re.IGNORECASE))
has_proper_join = bool(re.search(r'JOIN\s+departments\s+ON\s+students\.department_id\s+=\s+departments\.department_id', corrected, re.IGNORECASE))
has_group_by = bool(re.search(r'GROUP\s+BY\s+departments\.department_name', corrected, re.IGNORECASE))

print("Final SQL Quality:")
print(f"  1. No syntax errors (corruption): {not has_syntax_error} {'✅' if not has_syntax_error else '❌'}")
print(f"  2. Has proper JOIN: {has_proper_join} {'✅' if has_proper_join else '❌'}")
print(f"  3. Has complete GROUP BY: {has_group_by} {'✅' if has_group_by else '❌'}")

if not has_syntax_error and has_proper_join and has_group_by:
    print("\n✅ PERFECT! SQL is correct and executable")
else:
    print("\n❌ ISSUES - SQL will fail to execute")
    if has_syntax_error:
        print("   ERROR: SQL contains syntax corruption")
