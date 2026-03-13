import re

sql = "SELECT course_code FROM courses JOIN departments ON courses.department_id = departments.department_id WHERE departments.department_name = 'Mathematics'"

print("SQL:", sql)
print()

# Check for standalone HERE
standalone = re.search(r'\bHERE\b', sql, re.IGNORECASE)
print("Standalone HERE:", standalone)

# Check for concatenated HERE (not preceded by W)
concatenated = re.search(r'(?<!W)(\w)HERE\b', sql, re.IGNORECASE)
print("Concatenated HERE (not after W):", concatenated)
if concatenated:
    print("  Match:", concatenated.group())
    print("  Position:", concatenated.span())

# The issue: WHERE contains HERE, so we need to check the corrupted version instead
corrupted_sql = "SELECT course_code FROM courses W JOIN departments ON courses.department_id = departments.department_idHERE departments.department_name = 'Mathematics'"
print()
print("Corrupted SQL:", corrupted_sql)
print()

standalone_c = re.search(r'\bHERE\b', corrupted_sql, re.IGNORECASE)
print("Standalone HERE in corrupted:", standalone_c)

concatenated_c = re.search(r'(\w)HERE\b', corrupted_sql, re.IGNORECASE)
print("Concatenated HERE in corrupted:", concatenated_c)
if concatenated_c:
    print("  Match:", concatenated_c.group())
    print("  Char before HERE:", concatenated_c.group(1))
