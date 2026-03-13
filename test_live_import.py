#!/usr/bin/env python3
"""
Quick test to verify the fix is working in the actual imported module.
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

# Import directly to get the current state
from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

corrector = SQLPatternCorrector()

sql = "SELECT COUNT(*), departments.department_name FROM students G JOIN departments ON students.department_id = departments.department_idROUP BY GROUP BY departments.department_name"
question = "Count of students grouped by department"

schema_text = """
students: student_id, first_name, last_name, email, date_of_birth, enrollment_date, major, gpa, year_level, department_id
departments: department_id, department_name, building, budget
"""

foreign_keys = [
    ('students', 'department_id', 'departments', 'department_id')
]

print("Input SQL:")
print(sql)
print("\n" + "="*70 + "\n")

corrected = corrector.correct_sql(sql, question, schema_text, foreign_keys)

print("Corrected SQL:")
print(corrected)
print("\n" + "="*70 + "\n")

# Check if fixed
import re
has_g_join = bool(re.search(r'students\s+G\s+JOIN', corrected, re.IGNORECASE))
has_merged = bool(re.search(r'[a-fh-z0-9_]ROUP\s+BY', corrected, re.IGNORECASE))
has_duplicate = bool(re.search(r'GROUP\s+BY\s+GROUP\s+BY', corrected, re.IGNORECASE))
group_by_count = corrected.upper().count('GROUP BY')

print("Status:")
print(f"  Has 'students G JOIN': {has_g_join} {'❌' if has_g_join else '✅'}")
print(f"  Has merged 'idROUP BY': {has_merged} {'❌' if has_merged else '✅'}")
print(f"  Has duplicate GROUP BY: {has_duplicate} {'❌' if has_duplicate else '✅'}")
print(f"  GROUP BY count: {group_by_count} {'✅' if group_by_count == 1 else '❌'}")

if not has_g_join and not has_merged and not has_duplicate and group_by_count == 1:
    print("\n✅ ALL CHECKS PASSED - Fix is working!")
else:
    print("\n❌ SOME CHECKS FAILED - Fix may not be applied")
