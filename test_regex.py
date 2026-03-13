import re

question = "Show student names enrolled in Database Systems"

pattern = r'\b(?:enrolled in|taking|in course)\s+([A-Z]{2,6}\d{2,4}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'

match = re.search(pattern, question, re.IGNORECASE)

if match:
    print(f"✅ Match found: '{match.group(1)}'")
else:
    print("❌ No match")
    
# Try a simpler pattern
simple_pattern = r'\b(?:enrolled in|taking)\s+(.+?)(?:\s*$|\s+(?:department|course|and|or|with))'

match2 = re.search(simple_pattern, question, re.IGNORECASE)

if match2:
    print(f"✅ Simple match: '{match2.group(1)}'")
else:
    print("❌ No simple match")
