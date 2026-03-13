import sys
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Test query
question = "Show professor names hired after 2016"
sql = "SELECT hire_date FROM professors WHERE EXTRACT(YEAR FROM hire_date) > 2016"

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
selects_names = 'first_name' in corrected and 'last_name' in corrected
still_selects_hire_date = 'SELECT hire_date' in corrected
where_clause_correct = 'EXTRACT(YEAR FROM hire_date) > 2016' in corrected

print(f"  1. Selects first_name and last_name: {'✅' if selects_names else '❌'}")
print(f"  2. Still selects hire_date only: {'❌' if still_selects_hire_date else '✅'}")
print(f"  3. WHERE clause correct (EXTRACT): {'✅' if where_clause_correct else '❌'}")
print()

if selects_names and not still_selects_hire_date:
    print("✅ FULLY FIXED: Both SELECT and WHERE are correct")
elif where_clause_correct and not selects_names:
    print("⚠️  PARTIALLY FIXED: WHERE clause is correct, but SELECT clause needs fixing")
    print("   Expected: SELECT first_name, last_name FROM professors ...")
else:
    print("❌ ISSUE: Query needs fixes")
