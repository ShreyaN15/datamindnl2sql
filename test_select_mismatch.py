import sys
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Schema text format
schema_text = """
students: student_id, first_name, last_name, email, enrollment_date, gpa, department_id
professors: professor_id, first_name, last_name, email, office_location, department_id, hire_date
"""

foreign_keys = []

corrector = get_pattern_corrector()

# Test cases
test_cases = [
    {
        'name': 'Professor names - selects wrong column',
        'question': 'Show professor names hired after 2016',
        'sql': 'SELECT hire_date FROM professors WHERE EXTRACT(YEAR FROM hire_date) > 2016',
        'should_have': ['first_name', 'last_name']
    },
    {
        'name': 'Student names - selects wrong column',
        'question': 'List student names with GPA above 3.5',
        'sql': 'SELECT gpa FROM students WHERE gpa > 3.5',
        'should_have': ['first_name', 'last_name']
    },
    {
        'name': 'Show professors - implicit names',
        'question': 'Show professors',
        'sql': 'SELECT email FROM professors',
        'should_have': ['first_name', 'last_name']
    },
    {
        'name': 'List students - implicit names',
        'question': 'List students',
        'sql': 'SELECT student_id FROM students',
        'should_have': ['first_name', 'last_name']
    },
    {
        'name': 'Already correct - should not change',
        'question': 'Show professor names',
        'sql': 'SELECT first_name, last_name FROM professors',
        'should_have': ['first_name', 'last_name']
    },
]

print("=" * 70)
print("FIX #12: SELECT Clause Mismatch Tests")
print("=" * 70)
print()

all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    print(f"  Question: {test['question']}")
    print(f"  Original: {test['sql']}")
    
    corrected = corrector.correct_sql(test['sql'], test['question'], schema_text, foreign_keys)
    
    print(f"  Corrected: {corrected}")
    
    has_all_columns = all(col in corrected for col in test['should_have'])
    
    if has_all_columns:
        print(f"  ✅ PASS: SELECT includes {', '.join(test['should_have'])}")
    else:
        print(f"  ❌ FAIL: Expected {', '.join(test['should_have'])} in SELECT")
        all_passed = False
    
    print()

print("=" * 70)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
else:
    print("❌ SOME TESTS FAILED")
print("=" * 70)
