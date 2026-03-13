import sys
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Schema text format
schema_text = """
students: student_id, first_name, last_name, email, enrollment_date, gpa, department_id
departments: department_id, department_name, building_name, phone_number
enrollments: enrollment_id, student_id, course_id, semester, grade
courses: course_id, course_code, course_name, department_id, credits, professor_id
"""

foreign_keys = [
    ('students', 'department_id', 'departments', 'department_id'),
    ('enrollments', 'student_id', 'students', 'student_id'),
    ('enrollments', 'course_id', 'courses', 'course_id'),
    ('courses', 'department_id', 'departments', 'department_id'),
]

corrector = get_pattern_corrector()

# Test cases
test_cases = [
    {
        'name': 'Double quotes in WHERE',
        'question': 'List students in Computer Science',
        'sql': 'SELECT * FROM students WHERE department_name = "Computer Science"',
        'expect_single_quotes': True
    },
    {
        'name': 'Double quotes with special chars',
        'question': 'Find course',
        'sql': 'SELECT * FROM courses WHERE course_name = "Data Structures & Algorithms"',
        'expect_single_quotes': True
    },
    {
        'name': 'Multiple double-quoted strings',
        'question': 'Find students',
        'sql': 'SELECT * FROM students WHERE first_name = "John" AND last_name = "Smith"',
        'expect_single_quotes': True
    },
    {
        'name': 'Single quotes already (should not change)',
        'question': 'Find students',
        'sql': "SELECT * FROM students WHERE first_name = 'John'",
        'expect_single_quotes': True
    },
]

print("=" * 70)
print("FIX #10: Quote Normalization Tests")
print("=" * 70)
print()

all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    print(f"  Original: {test['sql']}")
    
    corrected = corrector.correct_sql(test['sql'], test['question'], schema_text, foreign_keys)
    
    print(f"  Corrected: {corrected}")
    
    has_double_quotes = '"' in corrected
    has_single_quotes = "'" in corrected
    
    if test['expect_single_quotes']:
        if has_single_quotes and not has_double_quotes:
            print(f"  ✅ PASS: Uses single quotes")
        else:
            print(f"  ❌ FAIL: Expected single quotes, found double quotes or none")
            all_passed = False
    
    print()

print("=" * 70)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
else:
    print("❌ SOME TESTS FAILED")
print("=" * 70)
