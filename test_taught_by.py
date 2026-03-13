import sys
import re
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Test query
question = "Show students taught by Grace Hopper"
sql = "SELECT first_name, last_name FROM students JOIN departments ON students.department_id = departments.department_id WHERE departments.department_name = 'Grace Hopper'"

# Schema text format
schema_text = """
students: student_id, first_name, last_name, email, enrollment_date, gpa, department_id
departments: department_id, department_name, building_name, phone_number
enrollments: enrollment_id, student_id, course_id, semester, grade
courses: course_id, course_code, course_name, department_id, credits, professor_id
professors: professor_id, first_name, last_name, email, office_location, department_id, hire_date
"""

foreign_keys = [
    ('students', 'department_id', 'departments', 'department_id'),
    ('enrollments', 'student_id', 'students', 'student_id'),
    ('enrollments', 'course_id', 'courses', 'course_id'),
    ('courses', 'department_id', 'departments', 'department_id'),
    ('courses', 'professor_id', 'professors', 'professor_id'),
    ('professors', 'department_id', 'departments', 'department_id'),
]

corrector = get_pattern_corrector()

print("=" * 70)
print(f"Question: {question}")
print(f"Generated SQL: {sql}")
print("=" * 70)

corrected = corrector.correct_sql(sql, question, schema_text, foreign_keys)

print(f"Corrected SQL: {corrected}")
print("=" * 70)
print()

# Analysis
print("📊 Analysis:")
has_professor_join = 'professors' in corrected.lower()
has_enrollments_join = 'enrollments' in corrected.lower()
has_courses_join = 'courses' in corrected.lower()
still_wrong_filter = "department_name = 'Grace Hopper'" in corrected
filters_by_professor = 'first_name' in corrected.lower() and 'last_name' in corrected.lower() and ('grace' in corrected.lower() or 'hopper' in corrected.lower())

print(f"  1. JOINs professors table: {'✅' if has_professor_join else '❌'}")
print(f"  2. JOINs enrollments table: {'✅' if has_enrollments_join else '❌'}")
print(f"  3. JOINs courses table: {'✅' if has_courses_join else '❌'}")
print(f"  4. No longer filters by department_name: {'✅' if not still_wrong_filter else '❌'}")
print(f"  5. Filters by professor name: {'✅' if filters_by_professor else '❌'}")
print()

if has_professor_join and has_enrollments_join and has_courses_join and not still_wrong_filter:
    print("✅ FIXED: Query properly connects students to professors")
else:
    print("❌ ISSUE: Fix #7 should detect 'taught by' pattern and fix this")
    print()
    print("Expected: students → enrollments → courses → professors")
    print("          WHERE professor.first_name = 'Grace' AND professor.last_name = 'Hopper'")
