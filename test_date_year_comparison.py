import sys
import re
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Test query
question = "Show professors hired after 2016"
sql = "SELECT hire_date FROM professors WHERE hire_date > 2016"

# Schema text format
schema_text = """
students: student_id, first_name, last_name, email, enrollment_date, gpa, department_id
departments: department_id, department_name, building_name, phone_number
enrollments: enrollment_id, student_id, course_id, semester, grade
courses: course_id, course_code, course_name, department_id, credits, professor_id
grades: grade_id, student_id, course_id, grade, semester
professors: professor_id, first_name, last_name, email, office_location, department_id, hire_date
"""

foreign_keys = [
    ('students', 'department_id', 'departments', 'department_id'),
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
has_year_comparison = '2016' in corrected
has_extract_year = 'EXTRACT(YEAR FROM' in corrected.upper() or 'EXTRACT (YEAR FROM' in corrected.upper()
has_date_string = "'2016" in corrected
still_has_type_error = re.match(r'.*\s+(hire_date|enrollment_date|date)\s*[><=]+\s*\d{4}\s*', corrected, re.IGNORECASE)

print(f"  1. Still has year comparison: {'✅' if has_year_comparison else '❌'}")
print(f"  2. Uses EXTRACT(YEAR FROM ...): {'✅' if has_extract_year else '❌'}")
print(f"  3. Uses date string (e.g., '2016-01-01'): {'✅' if has_date_string else '❌'}")
print(f"  4. Fixed type mismatch: {'✅' if not still_has_type_error else '❌'}")
print()

if has_extract_year or has_date_string:
    print("✅ FIXED: Type mismatch resolved")
else:
    print("❌ NOT FIXED: Still has date > integer comparison")
