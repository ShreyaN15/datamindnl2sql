#!/usr/bin/env python3
"""
Debug test to see step-by-step transformations
"""

import sys
import re
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

sql = "SELECT COUNT(*), departments.department_name FROM students G JOIN departments ON students.department_id = departments.department_idROUP BY GROUP BY departments.department_name"

print("Original SQL:")
print(sql)
print("\nExamining the corrupted section character by character:")
# Find the section around the corruption
idx = sql.find("department_id")
section = sql[idx:idx+80]
print(f"Section: '{section}'")
print(f"Characters: {[c for c in section[13:40]]}")  # Focus on "department_idROUP BY GROUP BY" part
print("\n" + "="*70 + "\n")

# Step 1: Fix merged text
sql_step1 = re.sub(r'(\w)ROUP\s+BY\b', r'\1 GROUP BY', sql, flags=re.IGNORECASE)
print("Step 1 - Fix merged text (idROUP BY → id GROUP BY):")
print(sql_step1)
print("\n" + "="*70 + "\n")

# Step 2: Fix merged ORDER BY  
sql_step2 = re.sub(r'(\w)RDER\s+BY\b', r'\1 ORDER BY', sql_step1, flags=re.IGNORECASE)
print("Step 2 - Fix merged ORDER BY:")
print(sql_step2)
print("\n" + "="*70 + "\n")

# Step 3: Fix standalone G before JOIN
sql_step3 = re.sub(r'\b(\w+)\s+G\s+JOIN\b', r'\1 JOIN', sql_step2, flags=re.IGNORECASE)
print("Step 3 - Fix standalone G before JOIN (students G JOIN → students JOIN):")
print(sql_step3)
print("\n" + "="*70 + "\n")

# Step 4: Fix duplicate GROUP BY
sql_step4 = re.sub(r'\bGROUP\s+BY\s+GROUP\s+BY\b', 'GROUP BY', sql_step3, flags=re.IGNORECASE)
print("Step 4 - Fix duplicate GROUP BY:")
print(sql_step4)
print("\n" + "="*70 + "\n")

# Check for remaining issues
print("Analysis:")
print(f"Has 'students G JOIN': {bool(re.search(r'students\\s+G\\s+JOIN', sql_step4, re.IGNORECASE))}")
print(f"Has 'idROUP BY': {bool(re.search(r'\\wROUP\\s+BY', sql_step4, re.IGNORECASE))}")
print(f"Has duplicate GROUP BY: {bool(re.search(r'GROUP\\s+BY\\s+GROUP\\s+BY', sql_step4, re.IGNORECASE))}")
print(f"GROUP BY count: {sql_step4.upper().count('GROUP BY')}")
