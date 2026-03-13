#!/usr/bin/env python3
"""
Test various ranking query patterns to ensure they're corrected properly.
"""

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

def test_ranking_queries():
    corrector = SQLPatternCorrector()
    
    # Schema text format
    schema_text = """
students: student_id, first_name, last_name, gpa
professors: professor_id, first_name, last_name, salary
courses: course_id, course_name, enrollment_count
    """
    
    test_cases = [
        {
            'name': 'Top 5 students by GPA',
            'question': 'Top 5 students by GPA',
            'input_sql': 'SELECT AVG(gpa) FROM students',
            'expected_patterns': ['ORDER BY', 'LIMIT 5', 'gpa', 'DESC'],
            'unexpected_patterns': ['AVG']
        },
        {
            'name': 'Bottom 3 students by GPA',
            'question': 'Bottom 3 students by GPA',
            'input_sql': 'SELECT MIN(gpa) FROM students',
            'expected_patterns': ['ORDER BY', 'LIMIT 3', 'gpa', 'ASC'],
            'unexpected_patterns': ['MIN']
        },
        {
            'name': 'Highest paid professor',
            'question': 'Highest paid professor',
            'input_sql': 'SELECT MAX(salary) FROM professors',
            'expected_patterns': ['ORDER BY', 'salary', 'DESC'],
            'unexpected_patterns': ['MAX']
        },
        {
            'name': 'Lowest paid professor',
            'question': 'Lowest paid professor',
            'input_sql': 'SELECT MIN(salary) FROM professors',
            'expected_patterns': ['ORDER BY', 'salary', 'ASC'],
            'unexpected_patterns': ['MIN']
        },
        {
            'name': 'Best 10 courses by enrollment',
            'question': 'Best 10 courses by enrollment',
            'input_sql': 'SELECT AVG(enrollment_count) FROM courses',
            'expected_patterns': ['ORDER BY', 'LIMIT 10', 'DESC'],
            'unexpected_patterns': ['AVG']
        },
        {
            'name': 'Top students (no number specified)',
            'question': 'Top students by GPA',
            'input_sql': 'SELECT SUM(gpa) FROM students',
            'expected_patterns': ['ORDER BY', 'gpa', 'DESC'],
            'unexpected_patterns': ['SUM']
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\n{'='*70}")
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
        
        # Check expected patterns
        all_expected_present = all(pattern.upper() in corrected.upper() for pattern in test['expected_patterns'])
        no_unexpected_present = all(pattern.upper() not in corrected.upper() for pattern in test['unexpected_patterns'])
        
        if all_expected_present and no_unexpected_present:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            if not all_expected_present:
                missing = [p for p in test['expected_patterns'] if p.upper() not in corrected.upper()]
                print(f"   Missing patterns: {missing}")
            if not no_unexpected_present:
                unwanted = [p for p in test['unexpected_patterns'] if p.upper() in corrected.upper()]
                print(f"   Unwanted patterns: {unwanted}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*70}")

if __name__ == '__main__':
    test_ranking_queries()
