#!/usr/bin/env python3
"""
Additional tests for various text corruption patterns.
"""

import sys
import re
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

def test_corruption_patterns():
    corrector = SQLPatternCorrector()
    
    schema_text = """
students: student_id, first_name, last_name, department_id
departments: department_id, department_name
courses: course_id, course_name
    """
    
    test_cases = [
        {
            'name': 'Merged GROUP BY (idROUP BY)',
            'sql': 'SELECT COUNT(*) FROM students GROUP BY department_idROUP BY',
            'should_not_contain_pattern': r'[a-fh-z0-9_]ROUP\s+BY',  # Check for merged text (not GROUP BY)
            'should_contain': ['GROUP BY'],
            'max_group_by': 1,
        },
        {
            'name': 'Standalone G before JOIN',
            'sql': 'SELECT * FROM students G JOIN departments ON students.department_id = departments.department_id',
            'should_not_contain': [' G JOIN', 'students G '],
            'should_contain': ['students JOIN'],
        },
        {
            'name': 'Valid GROUP BY (should not be changed)',
            'sql': 'SELECT department_id, COUNT(*) FROM students GROUP BY department_id',
            'should_contain': ['GROUP BY'],
            'max_group_by': 1,
        },
        {
            'name': 'W JOIN corruption',
            'sql': 'SELECT * FROM students W JOIN departments ON students.department_id = departments.department_id',
            'should_not_contain': ['W JOIN'],
            'should_contain': [' JOIN departments'],
        },
    ]
    
    print("Testing various text corruption patterns\n")
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"{'='*70}")
        print(f"Test: {test['name']}")
        print(f"Input:  {test['sql']}")
        
        corrected = corrector.correct_sql(
            test['sql'],
            "test query",
            schema_text,
            []
        )
        
        print(f"Output: {corrected}")
        
        # Check should_not_contain
        issues = []
        if 'should_not_contain' in test:
            for pattern in test['should_not_contain']:
                if pattern.upper() in corrected.upper():
                    issues.append(f"Should not contain '{pattern}'")
        
        # Check should_not_contain_pattern (regex)
        if 'should_not_contain_pattern' in test:
            if re.search(test['should_not_contain_pattern'], corrected, re.IGNORECASE):
                issues.append(f"Matches unwanted pattern: {test['should_not_contain_pattern']}")
        
        # Check should_contain
        if 'should_contain' in test:
            for pattern in test['should_contain']:
                if pattern.upper() not in corrected.upper():
                    issues.append(f"Should contain '{pattern}'")
        
        # Check GROUP BY count
        if 'max_group_by' in test:
            group_by_count = corrected.upper().count('GROUP BY')
            if group_by_count > test['max_group_by']:
                issues.append(f"Too many GROUP BY ({group_by_count}, max {test['max_group_by']})")
        
        if issues:
            print(f"❌ FAIL: {', '.join(issues)}")
            failed += 1
        else:
            print("✅ PASS")
            passed += 1
        print()
    
    print(f"{'='*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*70}")

if __name__ == '__main__':
    test_corruption_patterns()
