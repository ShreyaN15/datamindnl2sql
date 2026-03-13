#!/usr/bin/env python3
"""Test _remove_unnecessary_joins in isolation"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector
import re

sql = "SELECT T1.first_name, T1.last_name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T1.gpa > 3.5"

schema_tables = {
    'students': ['student_id', 'first_name', 'last_name', 'age', 'gpa'],
    'enrollments': ['enrollment_id', 'student_id', 'course_id']
}

print("Testing _remove_unnecessary_joins directly")
print("="*70)
print(f"Input: {sql}\n")

corrector = SQLPatternCorrector()
result = corrector._remove_unnecessary_joins(sql, schema_tables)

print(f"Output: {result}\n")

if result == sql:
    print("❌ NO CHANGE - JOIN not removed")
    print("\nLet me manually debug...")
    
    # Extract SELECT and WHERE
    select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE)
    where_match = re.search(r'WHERE\s+(.+?)(?:GROUP|ORDER|LIMIT|;|$)', sql, re.IGNORECASE)
    
    select_clause = select_match.group(1) if select_match else ""
    where_clause = where_match.group(1) if where_match else ""
    
    print(f"SELECT: {select_clause}")
    print(f"WHERE: {where_clause}")
    
    # Find column references
    referenced_columns = []
    for match in re.finditer(r'([a-zA-Z]\w*)\.(\w+)', select_clause + " " + where_clause):
        alias, col = match.groups()
        if not col.isdigit():
            referenced_columns.append(col.lower())
            print(f"  Found column: {col}")
    
    main_table_cols = ['student_id', 'first_name', 'last_name', 'age', 'gpa']
    print(f"\nReferenced: {set(referenced_columns)}")
    print(f"Main table has: {main_table_cols}")
    
    all_in_main = all(col in main_table_cols for col in set(referenced_columns))
    print(f"All in main table? {all_in_main}")
    print(f"Referenced columns list not empty? {bool(referenced_columns)}")
    
else:
    print("✅ SUCCESS - JOIN removed!")
    print(f"No JOIN in result: {'JOIN' not in result.upper()}")
