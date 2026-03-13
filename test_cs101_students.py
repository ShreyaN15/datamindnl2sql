#!/usr/bin/env python3
"""
Test: Show all students enrolled in CS101
Bug: WHERE T2.course_name when JOIN uses alias 'e', and course_name not in enrollments
Expected: Add JOIN to courses, use correct alias
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

def test_cs101_students():
    corrector = SQLPatternCorrector()
    
    question = "Show all students enrolled in CS101"
    
    # Bug: T2 alias doesn't exist (should be 'e'), and course_name not in enrollments
    generated_sql = "SELECT first_name, last_name FROM students JOIN enrollments e ON students.student_id = e.student_id WHERE T2.course_name = 'CS101'"
    
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
    print(f"  1. No T2 reference (should use 'e' or 'courses'): {'✅' if 'T2.' not in corrected else '❌'}")
    print(f"  2. Has JOIN to courses table: {'✅' if 'JOIN courses' in corrected.lower() else '❌'}")
    # Check either course_name or course_code is used
    has_course_filter = 'course_name' in corrected.lower() or 'course_code' in corrected.lower()
    print(f"  3. WHERE filters by course name/code: {'✅' if has_course_filter else '❌'}")
    print(f"  4. No 'enrollments.course_name': {'✅' if 'e.course_name' not in corrected and 'enrollments.course_name' not in corrected else '❌'}")
    
    print("\n✨ Expected: SELECT first_name, last_name FROM students JOIN enrollments e ON students.student_id = e.student_id JOIN courses ON e.course_id = courses.course_id WHERE courses.course_name = 'CS101'")

if __name__ == "__main__":
    test_cs101_students()
