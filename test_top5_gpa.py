#!/usr/bin/env python3
"""
Test case for: Top 5 students by GPA
Generated SQL: SELECT AVG(gpa) FROM students

Issues:
1. Uses AVG (aggregation) instead of selecting individual student GPAs
2. Missing ORDER BY gpa DESC
3. Missing LIMIT 5
4. Not selecting student identifying information (names)

Expected: SELECT first_name, last_name, gpa FROM students ORDER BY gpa DESC LIMIT 5
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

# Test data
question = "Top 5 students by GPA"
sql = "SELECT AVG(gpa) FROM students"

schema_text = """
students: student_id, first_name, last_name, email, date_of_birth, enrollment_date, major, gpa, year_level, department_id
"""

foreign_keys = []

print("=" * 70)
print(f"Question: {question}")
print(f"Generated SQL: {sql}")
print("=" * 70)
print()

# Apply pattern corrector
corrector = SQLPatternCorrector()
corrected = corrector.correct_sql(sql, question, schema_text, foreign_keys)

print(f"Corrected SQL: {corrected}")
print("=" * 70)
print()

# Analyze the correction
print("📊 Analysis:")

has_avg = 'AVG(' in corrected.upper()
has_order_by = 'ORDER BY' in corrected.upper()
has_limit = 'LIMIT' in corrected.upper()
has_student_names = 'first_name' in corrected.lower() or 'last_name' in corrected.lower()
has_gpa_column = 'gpa' in corrected.lower() and not corrected.lower().startswith('select avg(gpa)')

print(f"  1. No longer uses AVG (aggregate): {'✅' if not has_avg else '❌ Still uses AVG'}")
print(f"  2. Has ORDER BY: {'✅' if has_order_by else '❌ Missing ORDER BY'}")
print(f"  3. Has LIMIT 5: {'✅' if has_limit and '5' in corrected else '❌ Missing LIMIT'}")
print(f"  4. Selects student names: {'✅' if has_student_names else '❌ No student identification'}")
print(f"  5. Selects gpa column: {'✅' if has_gpa_column else '❌ No gpa in SELECT'}")

print()
if all([not has_avg, has_order_by, has_limit, has_student_names or has_gpa_column]):
    print("✅ FIXED: Query properly gets top students, not average")
else:
    print("❌ ISSUE: ML confused 'top by X' with aggregation")
    print()
    print("Expected: SELECT first_name, last_name, gpa FROM students")
    print("          ORDER BY gpa DESC LIMIT 5")
