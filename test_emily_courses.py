import sys
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Test query
question = "List all courses Emily Johnson is taking"
sql = "SELECT course_name FROM courses WHERE course_name = 'Emily Johnson'"

# Schema text format
schema_text = """
students: student_id, first_name, last_name, email, enrollment_date, gpa, department_id
departments: department_id, department_name, building_name, phone_number
enrollments: enrollment_id, student_id, course_id, semester, grade
courses: course_id, course_code, course_name, department_id, credits, professor_id
grades: grade_id, student_id, course_id, grade, semester
professors: professor_id, first_name, last_name, email, office_location, department_id
"""

# Foreign keys
foreign_keys = [
    ('students', 'department_id', 'departments', 'department_id'),
    ('enrollments', 'student_id', 'students', 'student_id'),
    ('enrollments', 'course_id', 'courses', 'course_id'),
    ('courses', 'department_id', 'departments', 'department_id'),
    ('courses', 'professor_id', 'professors', 'professor_id'),
    ('grades', 'student_id', 'students', 'student_id'),
    ('grades', 'course_id', 'courses', 'course_id'),
    ('professors', 'department_id', 'departments', 'department_id')
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
has_person_name = 'Emily Johnson' in corrected or 'Emily' in corrected
in_wrong_column = "course_name = 'Emily" in corrected
has_student_filter = 'first_name' in corrected.lower() or 'last_name' in corrected.lower()
has_enrollments = 'enrollments' in corrected.lower()
has_proper_joins = corrected.lower().count('join') >= 2

print(f"  1. Person name still in course_name: {'❌' if in_wrong_column else '✅'}")
print(f"  2. Filters by student name: {'✅' if has_student_filter else '❌'}")
print(f"  3. Has enrollments JOIN: {'✅' if has_enrollments else '❌'}")
print(f"  4. Has proper multi-table JOINs: {'✅' if has_proper_joins else '❌'}")
print()

if in_wrong_column:
    print("❌ BROKEN: Fix #7 should detect 'is taking' as enrollment context!")
else:
    print("✅ WORKING: Person name properly moved to student filter")
