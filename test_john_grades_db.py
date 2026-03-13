#!/usr/bin/env python3
"""
Test the corrected SQL against actual database
"""

import psycopg2

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="student_db",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

# Test the corrected SQL
sql = "SELECT g.* FROM students s JOIN grades g ON s.student_id = g.student_id WHERE s.first_name = 'John' AND s.last_name = 'Smith'"

print("Executing SQL:")
print(sql)
print()

try:
    cur.execute(sql)
    results = cur.fetchall()
    
    # Get column names
    colnames = [desc[0] for desc in cur.description]
    
    print(f"✅ Query executed successfully!")
    print(f"Found {len(results)} grade record(s) for John Smith")
    print()
    
    if results:
        print("Column names:", colnames)
        print("-" * 70)
        for row in results:
            print(row)
    else:
        print("No grades found for John Smith")
        
except Exception as e:
    print(f"❌ Query failed: {e}")
    
finally:
    cur.close()
    conn.close()
