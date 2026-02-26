-- Student Database Setup Script
-- This creates a comprehensive university database for demo purposes

-- Connect to student_db
\c student_db

-- Enable permissions for hari user
GRANT ALL PRIVILEGES ON SCHEMA public TO hari;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hari;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hari;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO hari;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO hari;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS grades CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS professors CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- Create departments table
CREATE TABLE departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    building VARCHAR(100),
    budget DECIMAL(12, 2),
    head_professor VARCHAR(100)
);

-- Create students table
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    date_of_birth DATE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    major VARCHAR(100),
    gpa DECIMAL(3, 2) CHECK (gpa >= 0 AND gpa <= 4.0),
    year_level INTEGER CHECK (year_level >= 1 AND year_level <= 4),
    department_id INTEGER REFERENCES departments(department_id)
);

-- Create professors table
CREATE TABLE professors (
    professor_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hire_date DATE,
    salary DECIMAL(10, 2),
    office_number VARCHAR(20),
    department_id INTEGER REFERENCES departments(department_id)
);

-- Create courses table
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    credits INTEGER CHECK (credits > 0),
    department_id INTEGER REFERENCES departments(department_id),
    professor_id INTEGER REFERENCES professors(professor_id),
    semester VARCHAR(20),
    max_students INTEGER DEFAULT 30
);

-- Create enrollments table
CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(student_id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(course_id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'active',
    UNIQUE(student_id, course_id)
);

-- Create grades table
CREATE TABLE grades (
    grade_id SERIAL PRIMARY KEY,
    enrollment_id INTEGER REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    assignment_name VARCHAR(100),
    score DECIMAL(5, 2),
    max_score DECIMAL(5, 2),
    grade_date DATE DEFAULT CURRENT_DATE,
    letter_grade VARCHAR(2)
);

-- Insert sample data for departments
INSERT INTO departments (department_name, building, budget, head_professor) VALUES
('Computer Science', 'Tech Building A', 500000.00, 'Dr. Alan Turing'),
('Mathematics', 'Science Hall', 350000.00, 'Dr. Emmy Noether'),
('Physics', 'Science Hall', 450000.00, 'Dr. Marie Curie'),
('Business Administration', 'Business Center', 400000.00, 'Dr. Peter Drucker'),
('English Literature', 'Humanities Building', 250000.00, 'Dr. Jane Austen');

-- Insert sample data for professors
INSERT INTO professors (first_name, last_name, email, hire_date, salary, office_number, department_id) VALUES
('Alan', 'Turing', 'a.turing@university.edu', '2015-08-15', 95000.00, 'TA-301', 1),
('Grace', 'Hopper', 'g.hopper@university.edu', '2016-01-10', 92000.00, 'TA-302', 1),
('Emmy', 'Noether', 'e.noether@university.edu', '2014-09-01', 88000.00, 'SH-201', 2),
('Carl', 'Gauss', 'c.gauss@university.edu', '2017-02-20', 85000.00, 'SH-202', 2),
('Marie', 'Curie', 'm.curie@university.edu', '2013-07-15', 98000.00, 'SH-301', 3),
('Richard', 'Feynman', 'r.feynman@university.edu', '2018-03-12', 90000.00, 'SH-302', 3),
('Peter', 'Drucker', 'p.drucker@university.edu', '2015-05-20', 87000.00, 'BC-101', 4),
('Warren', 'Buffett', 'w.buffett@university.edu', '2019-08-25', 89000.00, 'BC-102', 4),
('Jane', 'Austen', 'j.austen@university.edu', '2014-01-10', 82000.00, 'HB-201', 5),
('William', 'Shakespeare', 'w.shakespeare@university.edu', '2016-09-15', 84000.00, 'HB-202', 5);

-- Insert sample data for students
INSERT INTO students (first_name, last_name, email, date_of_birth, enrollment_date, major, gpa, year_level, department_id) VALUES
-- Computer Science students
('John', 'Smith', 'john.smith@student.edu', '2003-05-15', '2021-09-01', 'Computer Science', 3.8, 3, 1),
('Emily', 'Johnson', 'emily.johnson@student.edu', '2004-03-22', '2022-09-01', 'Computer Science', 3.9, 2, 1),
('Michael', 'Williams', 'michael.williams@student.edu', '2002-11-08', '2020-09-01', 'Computer Science', 3.5, 4, 1),
('Sarah', 'Brown', 'sarah.brown@student.edu', '2004-07-19', '2022-09-01', 'Computer Science', 3.7, 2, 1),
('David', 'Jones', 'david.jones@student.edu', '2003-09-30', '2021-09-01', 'Computer Science', 3.6, 3, 1),
-- Mathematics students
('Jessica', 'Garcia', 'jessica.garcia@student.edu', '2003-12-05', '2021-09-01', 'Mathematics', 3.9, 3, 2),
('Daniel', 'Martinez', 'daniel.martinez@student.edu', '2004-02-14', '2022-09-01', 'Mathematics', 3.4, 2, 2),
('Ashley', 'Rodriguez', 'ashley.rodriguez@student.edu', '2002-08-27', '2020-09-01', 'Mathematics', 3.7, 4, 2),
('Matthew', 'Davis', 'matthew.davis@student.edu', '2004-06-11', '2022-09-01', 'Mathematics', 3.8, 2, 2),
-- Physics students
('Amanda', 'Miller', 'amanda.miller@student.edu', '2003-04-03', '2021-09-01', 'Physics', 3.6, 3, 3),
('Christopher', 'Wilson', 'christopher.wilson@student.edu', '2004-10-18', '2022-09-01', 'Physics', 3.5, 2, 3),
('Brittany', 'Moore', 'brittany.moore@student.edu', '2002-01-25', '2020-09-01', 'Physics', 3.8, 4, 3),
-- Business students
('Joshua', 'Taylor', 'joshua.taylor@student.edu', '2003-07-09', '2021-09-01', 'Business Administration', 3.3, 3, 4),
('Megan', 'Anderson', 'megan.anderson@student.edu', '2004-11-21', '2022-09-01', 'Business Administration', 3.6, 2, 4),
('Brandon', 'Thomas', 'brandon.thomas@student.edu', '2002-03-16', '2020-09-01', 'Business Administration', 3.4, 4, 4),
-- English students
('Samantha', 'Jackson', 'samantha.jackson@student.edu', '2003-08-12', '2021-09-01', 'English Literature', 3.7, 3, 5),
('Nicholas', 'White', 'nicholas.white@student.edu', '2004-05-28', '2022-09-01', 'English Literature', 3.5, 2, 5),
('Lauren', 'Harris', 'lauren.harris@student.edu', '2002-12-07', '2020-09-01', 'English Literature', 3.9, 4, 5);

-- Insert sample data for courses
INSERT INTO courses (course_code, course_name, credits, department_id, professor_id, semester, max_students) VALUES
-- Computer Science courses
('CS101', 'Introduction to Programming', 4, 1, 1, 'Fall 2025', 40),
('CS201', 'Data Structures and Algorithms', 4, 1, 1, 'Spring 2026', 35),
('CS301', 'Database Systems', 3, 1, 2, 'Fall 2025', 30),
('CS401', 'Machine Learning', 4, 1, 2, 'Spring 2026', 25),
-- Mathematics courses
('MATH101', 'Calculus I', 4, 2, 3, 'Fall 2025', 50),
('MATH201', 'Linear Algebra', 3, 2, 4, 'Spring 2026', 40),
('MATH301', 'Abstract Algebra', 3, 2, 3, 'Fall 2025', 25),
-- Physics courses
('PHYS101', 'General Physics I', 4, 3, 5, 'Fall 2025', 45),
('PHYS201', 'Quantum Mechanics', 4, 3, 6, 'Spring 2026', 30),
('PHYS301', 'Thermodynamics', 3, 3, 5, 'Fall 2025', 28),
-- Business courses
('BUS101', 'Introduction to Business', 3, 4, 7, 'Fall 2025', 60),
('BUS201', 'Financial Accounting', 3, 4, 8, 'Spring 2026', 45),
('BUS301', 'Marketing Management', 3, 4, 7, 'Fall 2025', 35),
-- English courses
('ENG101', 'Composition and Rhetoric', 3, 5, 9, 'Fall 2025', 30),
('ENG201', 'American Literature', 3, 5, 10, 'Spring 2026', 28),
('ENG301', 'Shakespeare Studies', 3, 5, 10, 'Fall 2025', 25);

-- Insert sample data for enrollments
INSERT INTO enrollments (student_id, course_id, enrollment_date, status) VALUES
-- CS students enrollments
(1, 1, '2025-09-01', 'completed'), (1, 2, '2026-01-15', 'active'), (1, 5, '2025-09-01', 'completed'),
(2, 1, '2025-09-01', 'active'), (2, 3, '2025-09-01', 'active'), (2, 5, '2025-09-01', 'active'),
(3, 2, '2025-09-01', 'active'), (3, 4, '2026-01-15', 'active'), (3, 6, '2026-01-15', 'active'),
(4, 1, '2025-09-01', 'active'), (4, 3, '2025-09-01', 'active'),
(5, 1, '2025-09-01', 'completed'), (5, 2, '2026-01-15', 'active'), (5, 3, '2025-09-01', 'active'),
-- Math students enrollments
(6, 5, '2025-09-01', 'completed'), (6, 6, '2026-01-15', 'active'), (6, 7, '2025-09-01', 'active'),
(7, 5, '2025-09-01', 'active'), (7, 6, '2026-01-15', 'active'),
(8, 6, '2026-01-15', 'active'), (8, 7, '2025-09-01', 'completed'),
(9, 5, '2025-09-01', 'active'), (9, 7, '2025-09-01', 'active'),
-- Physics students enrollments
(10, 8, '2025-09-01', 'active'), (10, 9, '2026-01-15', 'active'), (10, 5, '2025-09-01', 'completed'),
(11, 8, '2025-09-01', 'active'), (11, 10, '2025-09-01', 'active'),
(12, 9, '2026-01-15', 'active'), (12, 10, '2025-09-01', 'completed'),
-- Business students enrollments
(13, 11, '2025-09-01', 'active'), (13, 12, '2026-01-15', 'active'), (13, 5, '2025-09-01', 'completed'),
(14, 11, '2025-09-01', 'active'), (14, 13, '2025-09-01', 'active'),
(15, 12, '2026-01-15', 'active'), (15, 13, '2025-09-01', 'completed'),
-- English students enrollments
(16, 14, '2025-09-01', 'active'), (16, 15, '2026-01-15', 'active'), (16, 5, '2025-09-01', 'completed'),
(17, 14, '2025-09-01', 'active'), (17, 16, '2025-09-01', 'active'),
(18, 15, '2026-01-15', 'active'), (18, 16, '2025-09-01', 'completed');

-- Insert sample data for grades
INSERT INTO grades (enrollment_id, assignment_name, score, max_score, grade_date, letter_grade) VALUES
-- Grades for student 1 (John Smith)
(1, 'Midterm Exam', 85, 100, '2025-10-15', 'B'),
(1, 'Final Project', 92, 100, '2025-12-10', 'A'),
(1, 'Quiz 1', 88, 100, '2025-09-20', 'B'),
(3, 'Midterm Exam', 78, 100, '2025-10-20', 'C'),
-- Grades for student 2 (Emily Johnson)
(4, 'Quiz 1', 95, 100, '2025-09-25', 'A'),
(4, 'Quiz 2', 90, 100, '2025-10-15', 'A'),
(5, 'Lab Report', 88, 100, '2025-10-01', 'B'),
-- Grades for student 3 (Michael Williams)
(7, 'Final Project', 82, 100, '2026-01-20', 'B'),
-- Grades for student 6 (Jessica Garcia)
(16, 'Midterm Exam', 94, 100, '2025-10-15', 'A'),
(16, 'Final Exam', 96, 100, '2025-12-15', 'A'),
(17, 'Quiz 1', 91, 100, '2026-01-25', 'A'),
-- Grades for student 8 (Ashley Rodriguez)
(21, 'Final Project', 89, 100, '2025-12-20', 'B');

-- Create indexes for better query performance
CREATE INDEX idx_students_department ON students(department_id);
CREATE INDEX idx_students_major ON students(major);
CREATE INDEX idx_students_gpa ON students(gpa);
CREATE INDEX idx_professors_department ON professors(department_id);
CREATE INDEX idx_courses_department ON courses(department_id);
CREATE INDEX idx_courses_professor ON courses(professor_id);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_grades_enrollment ON grades(enrollment_id);

-- Grant final permissions to hari
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hari;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hari;

-- Display summary
SELECT 'Database setup complete!' as message;
SELECT 'Total Departments: ' || COUNT(*) as summary FROM departments
UNION ALL
SELECT 'Total Professors: ' || COUNT(*) FROM professors
UNION ALL
SELECT 'Total Students: ' || COUNT(*) FROM students
UNION ALL
SELECT 'Total Courses: ' || COUNT(*) FROM courses
UNION ALL
SELECT 'Total Enrollments: ' || COUNT(*) FROM enrollments
UNION ALL
SELECT 'Total Grades: ' || COUNT(*) FROM grades;
