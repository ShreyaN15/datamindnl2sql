#!/usr/bin/env python3
"""
Test: List courses taken by John Smith
Bug: SELECT course_id FROM courses WHERE course_name = 'John Smith'
Expected: Join students -> enrollments -> courses and filter by student name
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

def test_courses_by_student():
    corrector = SQLPatternCorrector()
    
    question = "List courses taken by John Smith"
    
    # Bug: Looking for course_name = 'John Smith' instead of student name
    generated_sql = "SELECT course_id FROM courses WHERE course_name = 'John Smith'"
    
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
    print(f"  1. JOINs students table: {'✅' if 'students' in corrected.lower() else '❌'}")
    print(f"  2. JOINs enrollments table: {'✅' if 'enrollments' in corrected.lower() or 'enrollment' in corrected.lower() else '❌'}")
    bad_pattern = "course_name = 'John Smith'"
    print(f"  3. No 'course_name = John Smith': {'✅' if bad_pattern not in corrected else '❌'}")
    has_name_filter = 'first_name' in corrected.lower() or 'last_name' in corrected.lower()
    print(f"  4. Filters by student name: {'✅' if has_name_filter else '❌'}")
    
    print("\n✨ Expected pattern: SELECT ... FROM students/courses JOIN enrollments ... WHERE first_name = 'John' AND last_name = 'Smith'")

if __name__ == "__main__":
    test_courses_by_student()
