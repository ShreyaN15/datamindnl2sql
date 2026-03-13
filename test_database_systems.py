import sys
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Test query 1
question1 = "Show student names enrolled in Database Systems"
sql1 = "SELECT first_name, last_name FROM students JOIN enrollments e ON students.student_id = e.student_id"

# Test query 2
question2 = "Show students enrolled in Database Systems"
sql2 = "SELECT T1.student_id FROM enrollments AS T1 JOIN courses AS T2 ON T1.course_id = T2.course_id"

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
print("Query 1:")
print(f"Question: {question1}")
print(f"Generated SQL: {sql1}")
print("=" * 70)
corrected1 = corrector.correct_sql(sql1, question1, schema_text, foreign_keys)
print(f"Corrected SQL: {corrected1}")
print("=" * 70)
print()

print("=" * 70)
print("Query 2:")
print(f"Question: {question2}")
print(f"Generated SQL: {sql2}")
print("=" * 70)
corrected2 = corrector.correct_sql(sql2, question2, schema_text, foreign_keys)
print(f"Corrected SQL: {corrected2}")
print("=" * 70)
print()

# Analysis
print("📊 Analysis:")
print()
print("Query 1 Issues:")
has_courses_join1 = 'courses' in corrected1.lower()
has_where1 = 'WHERE' in corrected1.upper()
has_db_systems1 = 'Database Systems' in corrected1
print(f"  1. Has JOIN to courses table: {'✅' if has_courses_join1 else '❌'}")
print(f"  2. Has WHERE clause: {'✅' if has_where1 else '❌'}")
print(f"  3. Filters by 'Database Systems': {'✅' if has_db_systems1 else '❌'}")
print()

print("Query 2 Issues:")
has_where2 = 'WHERE' in corrected2.upper()
has_db_systems2 = 'Database Systems' in corrected2
print(f"  1. Has WHERE clause: {'✅' if has_where2 else '❌'}")
print(f"  2. Filters by 'Database Systems': {'✅' if has_db_systems2 else '❌'}")
print()

print("✨ Both queries need WHERE clause: WHERE course_name = 'Database Systems' (or similar)")
