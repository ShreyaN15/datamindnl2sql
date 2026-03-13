import sys
import re
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Schema text format
schema_text = """
students: student_id, first_name, last_name, email, enrollment_date, gpa, department_id
departments: department_id, department_name, building_name, phone_number
enrollments: enrollment_id, student_id, course_id, semester, grade
courses: course_id, course_code, course_name, department_id, credits, professor_id
professors: professor_id, first_name, last_name, email, office_location, department_id, hire_date
"""

foreign_keys = []

corrector = get_pattern_corrector()

# Test cases
test_cases = [
    {
        'name': 'Date > year',
        'question': 'Professors hired after 2016',
        'sql': 'SELECT * FROM professors WHERE hire_date > 2016',
        'should_extract': True
    },
    {
        'name': 'Date < year',
        'question': 'Students enrolled before 2020',
        'sql': 'SELECT * FROM students WHERE enrollment_date < 2020',
        'should_extract': True
    },
    {
        'name': 'Date = year',
        'question': 'Professors hired in 2015',
        'sql': 'SELECT * FROM professors WHERE hire_date = 2015',
        'should_extract': True
    },
    {
        'name': 'Date >= year',
        'question': 'Students enrolled from 2018',
        'sql': 'SELECT * FROM students WHERE enrollment_date >= 2018',
        'should_extract': True
    },
    {
        'name': 'Date <= year',
        'question': 'Professors hired until 2019',
        'sql': 'SELECT * FROM professors WHERE hire_date <= 2019',
        'should_extract': True
    },
    {
        'name': 'Qualified column (T1.hire_date)',
        'question': 'Professors hired after 2016',
        'sql': 'SELECT T1.first_name FROM professors AS T1 WHERE T1.hire_date > 2016',
        'should_extract': True
    },
    {
        'name': 'Multiple date comparisons',
        'question': 'Professors hired between 2015 and 2020',
        'sql': 'SELECT * FROM professors WHERE hire_date >= 2015 AND hire_date <= 2020',
        'should_extract': True
    },
]

print("=" * 70)
print("FIX #11: Date-Year Comparison Tests")
print("=" * 70)
print()

all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    print(f"  Original: {test['sql']}")
    
    corrected = corrector.correct_sql(test['sql'], test['question'], schema_text, foreign_keys)
    
    print(f"  Corrected: {corrected}")
    
    has_extract = 'EXTRACT(YEAR FROM' in corrected.upper() or 'EXTRACT (YEAR FROM' in corrected.upper()
    has_raw_comparison = bool(re.search(r'(hire_date|enrollment_date)\s*[><=]+\s*\d{4}(?!\))', corrected, re.IGNORECASE))
    
    if test['should_extract']:
        if has_extract and not has_raw_comparison:
            print(f"  ✅ PASS: Uses EXTRACT and no raw date-year comparison")
        else:
            print(f"  ❌ FAIL: Expected EXTRACT(YEAR FROM ...), still has raw comparison or missing EXTRACT")
            all_passed = False
    
    print()

print("=" * 70)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
else:
    print("❌ SOME TESTS FAILED")
print("=" * 70)
