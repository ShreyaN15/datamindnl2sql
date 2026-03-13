#!/usr/bin/env python3
"""
Test: Show students enrolled in Database Systems
Bug: JOIN ON course_id = course_id (ambiguous, should be T1.course_id = T2.course_id)
Expected: Proper table references in JOIN condition
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

def test_ambiguous_join():
    corrector = SQLPatternCorrector()
    
    question = "Show students enrolled in Database Systems"
    
    # Bug: Ambiguous JOIN condition
    generated_sql = "SELECT student_id FROM enrollments AS T1 JOIN courses AS T2 ON course_id = course_id"
    
    schema = """
    students: student_id, first_name, last_name, email, date_of_birth, gpa, department_id
    departments: department_id, department_name, building
    enrollments: enrollment_id, student_id, course_id, semester, grade
    courses: course_id, course_name, course_code, credits, professor_id
    grades: grade_id, student_id, course_id, grade, semester
    professors: professor_id, first_name, last_name, department_id, email
    """
    
    foreign_keys = [
        ("students", "department_id", "departments", "department_id"),
        ("enrollments", "student_id", "students", "student_id"),
        ("enrollments", "course_id", "courses", "course_id"),
        ("grades", "student_id", "students", "student_id"),
        ("grades", "course_id", "courses", "course_id"),
        ("professors", "department_id", "departments", "department_id"),
        ("courses", "professor_id", "professors", "professor_id")
    ]
    
    print("=" * 70)
    print(f"Question: {question}")
    print(f"Generated SQL: {generated_sql}")
    print("=" * 70)
    
    corrected = corrector.correct_sql(generated_sql, question, schema, foreign_keys)
    
    print(f"\nCorrected SQL: {corrected}")
    print("=" * 70)
    
    print("\n📊 Analysis:")
    # Check if JOIN has proper table references (case-insensitive)
    corrected_lower = corrected.lower()
    has_qualified_join = ('t1.course_id = t2.course_id' in corrected_lower or 
                         'enrollments.course_id = courses.course_id' in corrected_lower)
    print(f"  1. JOIN has qualified column references: {'✅' if has_qualified_join else '❌'}")
    
    # Check that ambiguous form is gone
    has_ambiguous = 'ON course_id = course_id' in corrected
    print(f"  2. No ambiguous 'ON course_id = course_id': {'✅' if not has_ambiguous else '❌'}")
    
    # Check if WHERE clause is added for 'Database Systems'
    has_where = 'WHERE' in corrected.upper() and 'Database Systems' in corrected
    print(f"  3. Has WHERE clause for 'Database Systems': {'✅' if has_where else '❌'}")
    
    print("\n✨ Expected: SELECT ... FROM enrollments T1 JOIN courses T2 ON T1.course_id = T2.course_id WHERE T2.course_name = 'Database Systems'")

if __name__ == "__main__":
    test_ambiguous_join()
