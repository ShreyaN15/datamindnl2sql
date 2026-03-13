import sys
sys.path.append('/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

# Schema text format
schema_text = """
professors: professor_id, first_name, last_name, email, office_location, department_id, hire_date
"""

foreign_keys = []

corrector = get_pattern_corrector()

# Original user query
question = "Show professor names hired after 2016"
# What the ML model generated (with Fix #11 already applied)
sql = "SELECT hire_date FROM professors WHERE EXTRACT(YEAR FROM hire_date) > 2016"

print("=" * 70)
print("COMPLETE FIX: Fixes #11 + #12 Working Together")
print("=" * 70)
print()
print(f"Question: {question}")
print(f"Generated SQL: {sql}")
print("=" * 70)

corrected = corrector.correct_sql(sql, question, schema_text, foreign_keys)

print(f"Corrected SQL: {corrected}")
print("=" * 70)
print()

# Analysis
print("📊 Complete Analysis:")
print()
print("Fix #11 (Date-Year Comparison):")
has_extract = 'EXTRACT(YEAR FROM hire_date)' in corrected
print(f"  ✅ Uses EXTRACT(YEAR FROM ...): {has_extract}")
print()

print("Fix #12 (SELECT Clause Mismatch):")
has_names = 'first_name' in corrected and 'last_name' in corrected
has_hire_date_only = corrected.strip().startswith('SELECT hire_date')
print(f"  ✅ Selects first_name, last_name: {has_names}")
print(f"  ✅ No longer selects only hire_date: {not has_hire_date_only}")
print()

print("Expected Final SQL:")
print("  SELECT first_name, last_name FROM professors")
print("  WHERE EXTRACT(YEAR FROM hire_date) > 2016")
print()

if has_extract and has_names and not has_hire_date_only:
    print("🎉 FULLY FIXED! Both Fix #11 and Fix #12 working correctly!")
    print()
    print("This query will now:")
    print("  1. Return professor names (not hire_date)")
    print("  2. Compare year properly (no type mismatch error)")
else:
    print("❌ Something is still wrong")
