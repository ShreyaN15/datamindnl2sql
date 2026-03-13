#!/usr/bin/env python3
"""Debug why _remove_unnecessary_joins isn't working"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector
import re

SCHEMA_TEXT = """
SCHEMA FOR student_db:
- students.student_id (PK)
- students.first_name
- students.last_name
- students.age
- students.gpa
"""

# After first two fixes, the SQL looks like this:
sql = "SELECT T1.first_name, T1.last_name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T1.gpa > 3.5"

print("Debugging _remove_unnecessary_joins")
print("="*70)
print(f"Input SQL: {sql}\n")

# Parse schema
schema_tables = {}
for line in SCHEMA_TEXT.strip().split('\n'):
    if line.startswith('- '):
        parts = line[2:].split('.')
        if len(parts) == 2:
            table, col_info = parts
            table = table.strip()
            col = col_info.split()[0].strip()
            if table not in schema_tables:
                schema_tables[table] = []
            schema_tables[table].append(col)

print(f"Schema tables: {schema_tables}\n")

# Find main table
from_match = re.search(r'FROM\s+(\w+)(?:\s+(?:AS\s+)?([A-Z0-9]+))?', sql, re.IGNORECASE)
if from_match:
    main_table = from_match.group(1).lower()
    main_alias = from_match.group(2) if from_match.group(2) else main_table
    print(f"Main table: {main_table}, alias: {main_alias}")

main_table_cols = [c.lower() for c in schema_tables.get(main_table, [])]
print(f"Main table columns: {main_table_cols}\n")

# Extract SELECT clause
select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE)
if select_match:
    select_clause = select_match.group(1)
    print(f"SELECT clause: {select_clause}")

# Extract WHERE clause
where_match = re.search(r'WHERE\s+(.+?)(?:GROUP|ORDER|LIMIT|;|$)', sql, re.IGNORECASE)
if where_match:
    where_clause = where_match.group(1)
    print(f"WHERE clause: {where_clause}")

# Find all column references
referenced_columns = []

# Pattern 1: alias.column
for match in re.finditer(r'(\w+)\.(\w+)', select_clause + " " + where_clause):
    alias, col = match.groups()
    referenced_columns.append(col.lower())
    print(f"  Found: {alias}.{col}")

print(f"\nReferenced columns: {set(referenced_columns)}")

# Check if all in main table
all_in_main_table = all(col in main_table_cols for col in set(referenced_columns))
print(f"All in main table? {all_in_main_table}")

if all_in_main_table:
    print("\nShould remove JOIN!")
else:
    print("\nShould keep JOIN")
    for col in set(referenced_columns):
        if col not in main_table_cols:
            print(f"  - Column '{col}' NOT in main table")
