#!/usr/bin/env python3
"""
Test that legitimate aggregation queries are NOT incorrectly "fixed".
These queries should remain unchanged because they're using aggregation correctly.
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

def test_legitimate_aggregations():
    corrector = SQLPatternCorrector()
    
    # Schema text format
    schema_text = """
students: student_id, first_name, last_name, gpa, department_id
departments: department_id, department_name
grades: grade_id, enrollment_id, grade_value
enrollments: enrollment_id, student_id, course_id
    """
    
    test_cases = [
        {
            'name': 'Average GPA per department (GROUP BY)',
            'question': 'What is the average GPA in each department?',
            'input_sql': 'SELECT department_id, AVG(gpa) FROM students GROUP BY department_id',
        },
        {
            'name': 'Total enrollment count',
            'question': 'How many students are enrolled?',
            'input_sql': 'SELECT COUNT(*) FROM enrollments',
        },
        {
            'name': 'Average grade value',
            'question': 'What is the average grade?',
            'input_sql': 'SELECT AVG(grade_value) FROM grades',
        },
        {
            'name': 'Sum with GROUP BY',
            'question': 'Total students per department',
            'input_sql': 'SELECT department_id, COUNT(*) FROM students GROUP BY department_id',
        },
    ]
    
    print("Testing legitimate aggregation queries (should NOT be changed)\n")
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"{'='*70}")
        print(f"Test: {test['name']}")
        print(f"Question: {test['question']}")
        print(f"Input SQL: {test['input_sql']}")
        
        corrected = corrector.correct_sql(
            test['input_sql'],
            test['question'],
            schema_text,
            []
        )
        
        print(f"Corrected SQL: {corrected}")
        
        # Check if SQL was changed (it shouldn't be for legitimate aggregations)
        # Allow minor changes like whitespace normalization
        input_normalized = ' '.join(test['input_sql'].upper().split())
        corrected_normalized = ' '.join(corrected.upper().split())
        
        if input_normalized == corrected_normalized:
            print("✅ PASS - Query unchanged (as expected)")
            passed += 1
        else:
            print("❌ FAIL - Query was incorrectly modified")
            failed += 1
        print()
    
    print(f"{'='*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*70}")

if __name__ == '__main__':
    test_legitimate_aggregations()
