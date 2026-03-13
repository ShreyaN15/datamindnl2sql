#!/usr/bin/env python3
"""
Test case for: Count of students grouped by department
Generated SQL with corruption: SELECT COUNT(*), departments.department_name FROM students G JOIN departments ON students.department_id = departments.department_idROUP BY GROUP BY departments.department_name

Issues:
1. "students G" - G is a fragment (from GROUP split)
2. "department_idROUP BY" - merged text (should be "department_id GROUP BY")
3. "GROUP BY GROUP BY" - duplicate GROUP BY

Expected: SELECT COUNT(*), departments.department_name FROM students JOIN departments ON students.department_id = departments.department_id GROUP BY departments.department_name
"""

import sys
import re
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

# Test data
question = "Count of students grouped by department"
sql = "SELECT COUNT(*), departments.department_name FROM students G JOIN departments ON students.department_id = departments.department_idROUP BY GROUP BY departments.department_name"

schema_text = """
students: student_id, first_name, last_name, email, date_of_birth, enrollment_date, major, gpa, year_level, department_id
departments: department_id, department_name, building, budget
"""

foreign_keys = [
    ('students', 'department_id', 'departments', 'department_id')
]

print("=" * 70)
print(f"Question: {question}")
print(f"Generated SQL: {sql}")
print("=" * 70)
print()

corrector = SQLPatternCorrector()
corrected_sql = corrector.correct_sql(sql, question, schema_text, foreign_keys)

print(f"Corrected SQL: {corrected_sql}")
print("=" * 70)
print()

# Analysis
print("📊 Analysis:")
issues = []

# Check 1: No standalone "G" before JOIN
if re.search(r'\bstudents\s+G\s+JOIN\b', corrected_sql, re.IGNORECASE):
    issues.append("  ❌ Still has 'students G JOIN' (should be 'students JOIN')")
else:
    print("  1. No standalone 'G' before JOIN: ✅")

# Check 2: No merged text like "department_idROUP" (check for word char + ROUP with no G before it)
# Properly formed is "GROUP BY" where ROUP is preceded by "G " not by another letter directly
if re.search(r'[a-fh-z0-9_]ROUP\s+BY\b', corrected_sql, re.IGNORECASE):
    issues.append("  ❌ Still has merged text like 'idROUP BY'")
else:
    print("  2. No merged text (department_idROUP): ✅")

# Check 3: No duplicate GROUP BY
if re.search(r'GROUP\s+BY\s+GROUP\s+BY', corrected_sql, re.IGNORECASE):
    issues.append("  ❌ Still has duplicate 'GROUP BY GROUP BY'")
else:
    print("  3. No duplicate GROUP BY: ✅")

# Check 4: Has single GROUP BY
if corrected_sql.upper().count('GROUP BY') == 1:
    print("  4. Has exactly one GROUP BY: ✅")
else:
    issues.append(f"  ❌ GROUP BY count is {corrected_sql.upper().count('GROUP BY')} (should be 1)")

# Check 5: Proper spacing around department_id
if re.search(r'department_id\s+GROUP\s+BY', corrected_sql, re.IGNORECASE):
    print("  5. Proper spacing around 'department_id GROUP BY': ✅")
else:
    issues.append("  ❌ Spacing issue around department_id and GROUP BY")

print()
if issues:
    print("❌ ISSUES FOUND:")
    for issue in issues:
        print(issue)
else:
    print("✅ FIXED: All corruption issues resolved")
