#!/usr/bin/env python3
"""
Run student_db golden questions through the full NL2SQL pipeline when a local model exists.

Usage (from repo root):
  python scripts/run_student_db_golden.py

If models/nl2sql-t5 is missing, exits 0 after printing a skip message.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLDEN_QUESTIONS = [
    "What are the courses offered by the Computer Science department?",
    "list the courses offered by Computer Science",
    "List courses in the Mathematics department",
    "Which courses are taken by John Smith?",
    "List students taking courses taught by Alan Turing",
    "Show all students enrolled in course code CS101",
    "List courses taught by Grace Hopper",
]


def main() -> int:
    model_path = ROOT / "models" / "nl2sql-t5"
    if not model_path.exists():
        print(f"Skipping full NL2SQL golden run: no model at {model_path}")
        print("Pattern-corrector tests: python -m unittest tests.test_student_db_corrector_golden -v")
        return 0

    from app.utils.schema_builder import build_schema_from_dict
    from app.engines.ml.nl2sql_service import get_nl2sql_service

    tables = {
        "departments": [
            "department_id",
            "department_name",
            "building",
            "budget",
            "head_professor",
        ],
        "students": [
            "student_id",
            "first_name",
            "last_name",
            "email",
            "department_id",
            "gpa",
        ],
        "professors": [
            "professor_id",
            "first_name",
            "last_name",
            "email",
            "department_id",
        ],
        "courses": [
            "course_id",
            "course_code",
            "course_name",
            "department_id",
            "professor_id",
        ],
        "enrollments": [
            "enrollment_id",
            "student_id",
            "course_id",
        ],
        "grades": [
            "grade_id",
            "enrollment_id",
            "assignment_name",
            "score",
        ],
    }
    fks = [
        ("students", "department_id", "departments", "department_id"),
        ("professors", "department_id", "departments", "department_id"),
        ("courses", "department_id", "departments", "department_id"),
        ("courses", "professor_id", "professors", "professor_id"),
        ("enrollments", "student_id", "students", "student_id"),
        ("enrollments", "course_id", "courses", "course_id"),
        ("grades", "enrollment_id", "enrollments", "enrollment_id"),
    ]
    schema_text, fk_list = build_schema_from_dict(tables, fks)

    svc = get_nl2sql_service()
    svc.load_model()

    for q in GOLDEN_QUESTIONS:
        sql = svc.generate_sql(
            q,
            schema_text,
            fk_list,
            use_sanitizer=True,
            use_enhancer=True,
            use_pattern_correction=True,
        )
        print(f"Q: {q}\nSQL: {sql}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
