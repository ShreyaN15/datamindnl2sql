#!/usr/bin/env python3
"""
Test case for: Students who scored above 90
Generated SQL: SELECT student_id FROM grades WHERE max_score > 90

Issues:
1. student_id doesn't exist in grades table (needs JOIN)
2. max_score is the maximum possible score, not actual score
Expected: Should select from students and join grades, filter by score > 90
"""

import sys
sys.path.insert(0, '/Users/harismac/Desktop/datamindnl2sql')

from app.engines.sql_validation.pattern_corrector import SQLPatternCorrector

# Test data
question = "Students who scored above 90"
sql = "SELECT student_id FROM grades WHERE max_score > 90"

schema_text = """
students: student_id, first_name, last_name, email, date_of_birth, enrollment_date, major, gpa, year_level, department_id
enrollments: enrollment_id, student_id, course_id, enrollment_date, status
grades: grade_id, enrollment_id, assignment_name, score, max_score, grade_date, letter_grade
courses: course_id, course_code, course_name, credits, department_id, professor_id, semester, max_students
professors: professor_id, first_name, last_name, email, hire_date, salary, office_number, department_id
departments: department_id, department_name, building, budget, head_professor
"""

foreign_keys = [
    ("students", "department_id", "departments", "department_id"),
    ("enrollments", "student_id", "students", "student_id"),
    ("enrollments", "course_id", "courses", "course_id"),
    ("grades", "enrollment_id", "enrollments", "enrollment_id"),
    ("courses", "department_id", "departments", "department_id"),
    ("courses", "professor_id", "professors", "professor_id"),
    ("professors", "department_id", "departments", "department_id"),
]

print("=" * 70)
print(f"Question: {question}")
print(f"Generated SQL: {sql}")
print("=" * 70)
print()

# Apply pattern corrector
corrector = SQLPatternCorrector()
corrected = corrector.correct_sql(sql, question, schema_text, foreign_keys)

print(f"Corrected SQL: {corrected}")
print("=" * 70)
print()

# Analyze the correction
print("📊 Analysis:")

has_students_join = 'students' in corrected.lower() and 'join' in corrected.lower()
has_enrollments_join = 'enrollments' in corrected.lower() and 'join' in corrected.lower()
has_grades_ref = 'grades' in corrected.lower()
uses_score_not_max = 'score' in corrected.lower() and corrected.lower().count('score') > corrected.lower().count('max_score')
no_student_id_from_grades = not ('student_id' in corrected and 'FROM grades' in corrected)

print(f"  1. JOINs students table: {'✅' if has_students_join else '❌'}")
print(f"  2. JOINs enrollments table: {'✅' if has_enrollments_join else '❌'}")
print(f"  3. References grades: {'✅' if has_grades_ref else '❌'}")
print(f"  4. Doesn't select non-existent student_id from grades: {'✅' if no_student_id_from_grades else '❌'}")

print()
if all([has_students_join, has_enrollments_join, no_student_id_from_grades]):
    print("✅ FIXED: Query properly joins tables to get students with scores")
else:
    print("❌ ISSUE: Should JOIN students ← enrollments ← grades")
    print()
    print("Expected: SELECT s.student_id, s.first_name, s.last_name")
    print("          FROM students s JOIN enrollments e ON s.student_id = e.student_id")
    print("          JOIN grades g ON e.enrollment_id = g.enrollment_id")
    print("          WHERE g.score > 90")
