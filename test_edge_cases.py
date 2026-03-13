#!/usr/bin/env python3
"""
Edge case test: "Top/ranking" words in question BUT with legitimate GROUP BY aggregation.
These should NOT be converted to ORDER BY since they have GROUP BY.
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

def test_edge_cases():
    corrector = SQLPatternCorrector()
    
    schema_text = """
students: student_id, first_name, last_name, gpa, department_id
departments: department_id, department_name
grades: grade_id, enrollment_id, grade_value
    """
    
    test_cases = [
        {
            'name': 'Top departments by average GPA (legitimate GROUP BY)',
            'question': 'What are the top departments by average GPA?',
            'input_sql': 'SELECT department_id, AVG(gpa) FROM students GROUP BY department_id ORDER BY AVG(gpa) DESC',
            'should_preserve': True,
        },
        {
            'name': 'Highest average grade per student (GROUP BY)',
            'question': 'What is the highest average grade per student?',
            'input_sql': 'SELECT student_id, AVG(grade_value) FROM grades GROUP BY student_id',
            'should_preserve': True,
        },
        {
            'name': 'Best student by GPA (no GROUP BY - should fix)',
            'question': 'Who is the best student by GPA?',
            'input_sql': 'SELECT AVG(gpa) FROM students',
            'should_preserve': False,
        },
    ]
    
    print("Testing edge cases with ranking words + GROUP BY\n")
    
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
        
        # Check if aggregation was preserved
        input_has_agg = bool(__import__('re').search(r'\b(AVG|SUM|COUNT|MIN|MAX)\s*\(', test['input_sql'].upper()))
        corrected_has_agg = bool(__import__('re').search(r'\b(AVG|SUM|COUNT|MIN|MAX)\s*\(', corrected.upper()))
        
        if test['should_preserve']:
            if input_has_agg and corrected_has_agg:
                print("✅ PASS - Aggregation preserved (as expected)")
            else:
                print("❌ FAIL - Aggregation removed incorrectly")
        else:
            if input_has_agg and not corrected_has_agg:
                print("✅ PASS - Aggregation removed and replaced with ORDER BY (as expected)")
            else:
                print("❌ FAIL - Aggregation should have been removed")
        print()

if __name__ == '__main__':
    test_edge_cases()
