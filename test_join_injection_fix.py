#!/usr/bin/env python3
"""
Test the JOIN injection fix - ensure it doesn't create GROUP corruption.
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

corrector = SQLPatternCorrector()

# Test case: SQL that needs JOIN injection but has GROUP BY
sql = "SELECT COUNT(*), departments.department_name FROM students GROUP BY"
question = "Count of students grouped by department"

schema_text = """
students: student_id, first_name, last_name, email, date_of_birth, enrollment_date, major, gpa, year_level, department_id
departments: department_id, department_name, building, budget
"""

foreign_keys = [
    ('students', 'department_id', 'departments', 'department_id')
]

print("="*70)
print("Testing JOIN injection with GROUP BY")
print("="*70)
print(f"Original SQL: {sql}")
print()

corrected = corrector.correct_sql(sql, question, schema_text, foreign_keys)

print(f"Corrected SQL: {corrected}")
print("="*70)
print()

# Analysis
import re

has_g_join = bool(re.search(r'students\s+G\s+JOIN', corrected, re.IGNORECASE))
has_merged = bool(re.search(r'[a-fh-z0-9_]ROUP\s+BY', corrected, re.IGNORECASE))
has_duplicate_group = bool(re.search(r'GROUP\s+BY\s+GROUP\s+BY', corrected, re.IGNORECASE))
has_join = bool(re.search(r'JOIN\s+departments', corrected, re.IGNORECASE))
has_group_by = 'GROUP BY' in corrected.upper()

print("Analysis:")
print(f"  1. Has JOIN to departments: {has_join} {'✅' if has_join else '❌'}")
print(f"  2. No 'students G JOIN' corruption: {not has_g_join} {'✅' if not has_g_join else '❌'}")
print(f"  3. No merged 'idROUP BY': {not has_merged} {'✅' if not has_merged else '❌'}")
print(f"  4. No duplicate GROUP BY: {not has_duplicate_group} {'✅' if not has_duplicate_group else '❌'}")
print(f"  5. Has GROUP BY clause: {has_group_by} {'✅' if has_group_by else '❌'}")

if has_join and not has_g_join and not has_merged and not has_duplicate_group and has_group_by:
    print("\n✅ PERFECT! JOIN injected correctly without creating corruption")
else:
    print("\n❌ ISSUES FOUND")
