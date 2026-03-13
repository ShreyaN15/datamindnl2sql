import sys
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Test query
question = "List professor names in Computer Science department"
sql = 'SELECT T1.first_name, T1.last_name FROM professors AS T1 JOIN departments AS T2 ON T1.department_id = T2.department_id WHERE T2.department_name = "Computer Science"'

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
has_double_quotes = '"' in corrected
has_single_quotes = "'" in corrected and "Computer Science" in corrected
proper_join = 'T1.department_id = T2.department_id' in corrected or 't1.department_id = t2.department_id' in corrected.lower()
filters_correctly = 'department_name' in corrected.lower() and 'Computer Science' in corrected

print(f"  1. Uses double quotes for strings: {'❌' if has_double_quotes else '✅'}")
print(f"  2. Uses single quotes for strings: {'✅' if has_single_quotes else '❌'}")
print(f"  3. Has proper JOIN condition: {'✅' if proper_join else '❌'}")
print(f"  4. Filters by department_name: {'✅' if filters_correctly else '❌'}")
print()

if has_double_quotes:
    print("⚠️  ISSUE: SQL uses double quotes instead of single quotes for string literals")
    print("   PostgreSQL may accept this but it's non-standard and can fail in strict modes")
else:
    print("✅ Query looks good!")
