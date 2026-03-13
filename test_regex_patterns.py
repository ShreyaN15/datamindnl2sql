#!/usr/bin/env python3
"""Test regex for JOIN removal"""

import re

sql = "SELECT T1.first_name, T1.last_name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T1.gpa > 3.5"

print("Testing regex patterns for JOIN removal")
print("="*70)
print(f"Original: {sql}\n")

# Pattern 1: My current pattern
pattern1 = r'\s+JOIN\s+[\w\s]+\s+ON\s+[\w\s.=]+\s+(?=WHERE|GROUP|ORDER|LIMIT|;|$)'
result1 = re.sub(pattern1, ' ', sql, flags=re.IGNORECASE)
print(f"Pattern 1: {pattern1}")
print(f"Result: {result1}")
print(f"Changed: {result1 != sql}\n")

# Pattern 2: More specific
pattern2 = r'\s+JOIN\s+\w+\s+AS\s+\w+\s+ON\s+[^W]+(?=WHERE)'
result2 = re.sub(pattern2, ' ', sql, flags=re.IGNORECASE)
print(f"Pattern 2: {pattern2}")
print(f"Result: {result2}")
print(f"Changed: {result2 != sql}\n")

# Pattern 3: Even simpler - match from JOIN to just before WHERE
pattern3 = r'JOIN\s+enrollments\s+AS\s+T2\s+ON\s+T1\.student_id\s*=\s*T2\.student_id\s+'
result3 = re.sub(pattern3, '', sql, flags=re.IGNORECASE)
print(f"Pattern 3: {pattern3}")
print(f"Result: {result3}")
print(f"Changed: {result3 != sql}\n")

# Pattern 4: Generic - remove from JOIN to before WHERE
pattern4 = r'\s+JOIN[^W]+WHERE'
result4 = re.sub(pattern4, ' WHERE', sql, flags=re.IGNORECASE)
print(f"Pattern 4: {pattern4}")
print(f"Result: {result4}")
print(f"Changed: {result4 != sql}\n")

# Check if 'W' in WHERE is causing issues
print(f"Note: '[^W]' means 'not W' - but WHERE starts with W!")
print(f"So patterns using [^W] will NOT work")
