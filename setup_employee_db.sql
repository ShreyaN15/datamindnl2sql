-- ============================================================================
-- EMPLOYEE DATABASE SCHEMA
-- A comprehensive employee management system with departments, projects, 
-- salaries, performance reviews, and team assignments
-- ============================================================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS performance_reviews CASCADE;
DROP TABLE IF EXISTS project_assignments CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS salary_history CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS locations CASCADE;

-- ============================================================================
-- TABLE: locations
-- Physical office locations
-- ============================================================================
CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50),
    country VARCHAR(100) NOT NULL,
    office_address VARCHAR(255)
);

-- ============================================================================
-- TABLE: departments
-- Company departments
-- ============================================================================
CREATE TABLE departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    location_id INTEGER REFERENCES locations(location_id),
    budget DECIMAL(12, 2),
    head_employee_id INTEGER  -- Will be set after employees are created
);

-- ============================================================================
-- TABLE: employees
-- Employee information
-- ============================================================================
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    department_id INTEGER REFERENCES departments(department_id),
    manager_id INTEGER REFERENCES employees(employee_id),
    current_salary DECIMAL(10, 2) NOT NULL,
    employment_status VARCHAR(20) DEFAULT 'Active',
    birth_date DATE
);

-- ============================================================================
-- TABLE: salary_history
-- Historical salary records for employees
-- ============================================================================
CREATE TABLE salary_history (
    salary_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
    salary_amount DECIMAL(10, 2) NOT NULL,
    effective_date DATE NOT NULL,
    end_date DATE,
    change_reason VARCHAR(100)
);

-- ============================================================================
-- TABLE: projects
-- Company projects
-- ============================================================================
CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    budget DECIMAL(12, 2),
    status VARCHAR(50) DEFAULT 'Active',
    department_id INTEGER REFERENCES departments(department_id)
);

-- ============================================================================
-- TABLE: project_assignments
-- Employee assignments to projects
-- ============================================================================
CREATE TABLE project_assignments (
    assignment_id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
    role VARCHAR(100),
    assigned_date DATE NOT NULL,
    hours_allocated DECIMAL(5, 2),
    UNIQUE(project_id, employee_id)
);

-- ============================================================================
-- TABLE: performance_reviews
-- Employee performance reviews
-- ============================================================================
CREATE TABLE performance_reviews (
    review_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
    review_date DATE NOT NULL,
    reviewer_id INTEGER REFERENCES employees(employee_id),
    rating DECIMAL(3, 2) CHECK (rating >= 1.0 AND rating <= 5.0),
    comments TEXT,
    review_period VARCHAR(50)
);

-- ============================================================================
-- INSERT DATA: locations
-- ============================================================================
INSERT INTO locations (city, state, country, office_address) VALUES
('San Francisco', 'CA', 'USA', '123 Tech Boulevard'),
('New York', 'NY', 'USA', '456 Finance Street'),
('Austin', 'TX', 'USA', '789 Innovation Drive'),
('Seattle', 'WA', 'USA', '321 Cloud Avenue'),
('Boston', 'MA', 'USA', '654 Research Parkway');

-- ============================================================================
-- INSERT DATA: departments
-- ============================================================================
INSERT INTO departments (department_name, location_id, budget, head_employee_id) VALUES
('Engineering', 1, 2500000.00, NULL),
('Sales', 2, 1800000.00, NULL),
('Marketing', 1, 1200000.00, NULL),
('Human Resources', 3, 800000.00, NULL),
('Finance', 2, 1500000.00, NULL),
('Product Management', 1, 1400000.00, NULL),
('Customer Support', 4, 900000.00, NULL),
('Operations', 3, 1100000.00, NULL);

-- ============================================================================
-- INSERT DATA: employees
-- ============================================================================
INSERT INTO employees (first_name, last_name, email, phone, hire_date, job_title, department_id, manager_id, current_salary, employment_status, birth_date) VALUES
-- Engineering Department
('Sarah', 'Johnson', 'sarah.johnson@company.com', '555-0101', '2018-03-15', 'VP of Engineering', 1, NULL, 185000.00, 'Active', '1985-06-12'),
('Michael', 'Chen', 'michael.chen@company.com', '555-0102', '2019-01-10', 'Senior Software Engineer', 1, 1, 135000.00, 'Active', '1988-09-23'),
('Emily', 'Rodriguez', 'emily.rodriguez@company.com', '555-0103', '2020-06-01', 'Software Engineer', 1, 1, 110000.00, 'Active', '1992-03-17'),
('James', 'Wilson', 'james.wilson@company.com', '555-0104', '2021-02-15', 'DevOps Engineer', 1, 1, 125000.00, 'Active', '1990-11-08'),
('Aisha', 'Patel', 'aisha.patel@company.com', '555-0105', '2019-08-20', 'Lead QA Engineer', 1, 1, 115000.00, 'Active', '1987-05-30'),

-- Sales Department
('Robert', 'Thompson', 'robert.thompson@company.com', '555-0201', '2017-05-10', 'VP of Sales', 2, NULL, 175000.00, 'Active', '1983-12-01'),
('Lisa', 'Martinez', 'lisa.martinez@company.com', '555-0202', '2019-03-12', 'Senior Account Executive', 2, 6, 128000.00, 'Active', '1989-07-14'),
('David', 'Lee', 'david.lee@company.com', '555-0203', '2020-09-01', 'Account Executive', 2, 6, 95000.00, 'Active', '1993-01-25'),
('Jennifer', 'White', 'jennifer.white@company.com', '555-0204', '2021-01-15', 'Sales Development Rep', 2, 6, 75000.00, 'Active', '1995-08-19'),
('Carlos', 'Garcia', 'carlos.garcia@company.com', '555-0205', '2018-11-20', 'Enterprise Sales Manager', 2, 6, 142000.00, 'Active', '1986-04-07'),

-- Marketing Department
('Amanda', 'Taylor', 'amanda.taylor@company.com', '555-0301', '2018-07-01', 'VP of Marketing', 3, NULL, 165000.00, 'Active', '1984-10-22'),
('Kevin', 'Brown', 'kevin.brown@company.com', '555-0302', '2019-09-15', 'Marketing Manager', 3, 11, 105000.00, 'Active', '1990-02-28'),
('Nina', 'Anderson', 'nina.anderson@company.com', '555-0303', '2020-04-10', 'Content Marketing Specialist', 3, 11, 82000.00, 'Active', '1992-12-05'),
('Thomas', 'Moore', 'thomas.moore@company.com', '555-0304', '2021-06-01', 'Digital Marketing Coordinator', 3, 11, 68000.00, 'Active', '1994-09-18'),

-- Human Resources
('Patricia', 'Harris', 'patricia.harris@company.com', '555-0401', '2017-02-15', 'VP of Human Resources', 4, NULL, 155000.00, 'Active', '1982-03-14'),
('Daniel', 'Clark', 'daniel.clark@company.com', '555-0402', '2019-05-20', 'HR Manager', 4, 15, 98000.00, 'Active', '1988-11-30'),
('Sophie', 'Lewis', 'sophie.lewis@company.com', '555-0403', '2020-10-05', 'Recruiter', 4, 15, 72000.00, 'Active', '1991-06-21'),

-- Finance
('William', 'Walker', 'william.walker@company.com', '555-0501', '2016-09-01', 'CFO', 5, NULL, 195000.00, 'Active', '1980-08-16'),
('Rachel', 'Hall', 'rachel.hall@company.com', '555-0502', '2018-12-10', 'Senior Financial Analyst', 5, 18, 118000.00, 'Active', '1987-04-09'),
('Andrew', 'Young', 'andrew.young@company.com', '555-0503', '2020-02-20', 'Accountant', 5, 18, 85000.00, 'Active', '1990-10-12'),
('Maria', 'King', 'maria.king@company.com', '555-0504', '2021-03-15', 'Financial Analyst', 5, 18, 78000.00, 'Active', '1993-07-27'),

-- Product Management
('Christopher', 'Wright', 'christopher.wright@company.com', '555-0601', '2017-11-05', 'VP of Product', 6, NULL, 172000.00, 'Active', '1983-05-19'),
('Jessica', 'Lopez', 'jessica.lopez@company.com', '555-0602', '2019-04-18', 'Senior Product Manager', 6, 22, 132000.00, 'Active', '1988-01-11'),
('Brandon', 'Hill', 'brandon.hill@company.com', '555-0603', '2020-08-25', 'Product Manager', 6, 22, 108000.00, 'Active', '1991-09-03'),
('Olivia', 'Scott', 'olivia.scott@company.com', '555-0604', '2021-05-10', 'Associate Product Manager', 6, 22, 92000.00, 'Active', '1994-02-15'),

-- Customer Support
('Matthew', 'Green', 'matthew.green@company.com', '555-0701', '2018-04-12', 'Director of Support', 7, NULL, 125000.00, 'Active', '1986-12-08'),
('Ashley', 'Adams', 'ashley.adams@company.com', '555-0702', '2019-10-08', 'Support Team Lead', 7, 26, 88000.00, 'Active', '1990-08-24'),
('Ryan', 'Baker', 'ryan.baker@company.com', '555-0703', '2020-11-15', 'Support Specialist', 7, 26, 65000.00, 'Active', '1993-04-16'),
('Lauren', 'Nelson', 'lauren.nelson@company.com', '555-0704', '2021-07-20', 'Support Specialist', 7, 26, 62000.00, 'Active', '1995-11-02'),

-- Operations
('Jonathan', 'Carter', 'jonathan.carter@company.com', '555-0801', '2017-08-15', 'VP of Operations', 8, NULL, 168000.00, 'Active', '1984-07-29'),
('Michelle', 'Mitchell', 'michelle.mitchell@company.com', '555-0802', '2019-06-22', 'Operations Manager', 8, 30, 102000.00, 'Active', '1989-03-06'),
('Eric', 'Perez', 'eric.perez@company.com', '555-0803', '2020-12-01', 'Operations Coordinator', 8, 30, 71000.00, 'Active', '1992-10-20'),
('Samantha', 'Roberts', 'samantha.roberts@company.com', '555-0804', '2021-09-05', 'Operations Analyst', 8, 30, 68000.00, 'Active', '1994-05-14');

-- Update department heads
UPDATE departments SET head_employee_id = 1 WHERE department_name = 'Engineering';
UPDATE departments SET head_employee_id = 6 WHERE department_name = 'Sales';
UPDATE departments SET head_employee_id = 11 WHERE department_name = 'Marketing';
UPDATE departments SET head_employee_id = 15 WHERE department_name = 'Human Resources';
UPDATE departments SET head_employee_id = 18 WHERE department_name = 'Finance';
UPDATE departments SET head_employee_id = 22 WHERE department_name = 'Product Management';
UPDATE departments SET head_employee_id = 26 WHERE department_name = 'Customer Support';
UPDATE departments SET head_employee_id = 30 WHERE department_name = 'Operations';

-- ============================================================================
-- INSERT DATA: salary_history
-- ============================================================================
INSERT INTO salary_history (employee_id, salary_amount, effective_date, end_date, change_reason) VALUES
-- Sample salary history for select employees
(1, 165000.00, '2018-03-15', '2020-03-15', 'Initial hire'),
(1, 175000.00, '2020-03-15', '2022-03-15', 'Annual raise'),
(1, 185000.00, '2022-03-15', NULL, 'Promotion'),

(2, 115000.00, '2019-01-10', '2021-01-10', 'Initial hire'),
(2, 125000.00, '2021-01-10', '2023-01-10', 'Performance raise'),
(2, 135000.00, '2023-01-10', NULL, 'Senior promotion'),

(6, 155000.00, '2017-05-10', '2020-05-10', 'Initial hire'),
(6, 165000.00, '2020-05-10', '2023-05-10', 'Annual raise'),
(6, 175000.00, '2023-05-10', NULL, 'Performance bonus'),

(18, 175000.00, '2016-09-01', '2019-09-01', 'Initial hire'),
(18, 185000.00, '2019-09-01', '2022-09-01', 'Annual raise'),
(18, 195000.00, '2022-09-01', NULL, 'Market adjustment');

-- ============================================================================
-- INSERT DATA: projects
-- ============================================================================
INSERT INTO projects (project_name, description, start_date, end_date, budget, status, department_id) VALUES
('Mobile App Redesign', 'Complete redesign of mobile application', '2024-01-15', '2024-06-30', 450000.00, 'Active', 1),
('Customer Portal v2', 'New customer self-service portal', '2024-02-01', '2024-08-31', 380000.00, 'Active', 1),
('Q1 Sales Campaign', 'Major sales push for Q1 2024', '2024-01-01', '2024-03-31', 250000.00, 'Completed', 2),
('Brand Refresh', 'Company rebrand initiative', '2023-11-01', '2024-04-30', 320000.00, 'Active', 3),
('HRIS Implementation', 'New HR information system', '2024-03-01', '2024-09-30', 280000.00, 'Active', 4),
('Financial Audit', 'Annual financial audit', '2024-02-15', '2024-05-15', 180000.00, 'Active', 5),
('Product Launch - AI Features', 'Launch of new AI-powered features', '2024-01-10', '2024-07-31', 520000.00, 'Active', 6),
('Support Chatbot', 'AI-powered support chatbot', '2024-02-20', '2024-06-20', 210000.00, 'Active', 7),
('Process Optimization', 'Streamline operational processes', '2024-01-05', '2024-12-31', 340000.00, 'Active', 8);

-- ============================================================================
-- INSERT DATA: project_assignments
-- ============================================================================
INSERT INTO project_assignments (project_id, employee_id, role, assigned_date, hours_allocated) VALUES
-- Mobile App Redesign
(1, 2, 'Technical Lead', '2024-01-15', 30.0),
(1, 3, 'Backend Developer', '2024-01-15', 35.0),
(1, 4, 'DevOps', '2024-01-20', 15.0),
(1, 5, 'QA Lead', '2024-01-22', 25.0),

-- Customer Portal v2
(2, 2, 'Architect', '2024-02-01', 20.0),
(2, 3, 'Lead Developer', '2024-02-01', 40.0),

-- Q1 Sales Campaign
(3, 7, 'Campaign Lead', '2024-01-01', 30.0),
(3, 8, 'Sales Rep', '2024-01-01', 35.0),
(3, 9, 'Sales Rep', '2024-01-01', 35.0),

-- Brand Refresh
(4, 12, 'Project Manager', '2023-11-01', 25.0),
(4, 13, 'Content Lead', '2023-11-01', 30.0),
(4, 14, 'Marketing Coordinator', '2023-11-01', 20.0),

-- HRIS Implementation
(5, 16, 'Project Manager', '2024-03-01', 20.0),
(5, 17, 'HR Coordinator', '2024-03-01', 15.0),

-- Product Launch - AI Features
(7, 23, 'Product Lead', '2024-01-10', 35.0),
(7, 24, 'Product Manager', '2024-01-10', 30.0),
(7, 2, 'Tech Advisor', '2024-01-15', 10.0),

-- Support Chatbot
(8, 27, 'Support Lead', '2024-02-20', 20.0),
(8, 28, 'Support Specialist', '2024-02-20', 15.0),
(8, 3, 'Developer', '2024-02-25', 25.0);

-- ============================================================================
-- INSERT DATA: performance_reviews
-- ============================================================================
INSERT INTO performance_reviews (employee_id, review_date, reviewer_id, rating, comments, review_period) VALUES
-- Engineering reviews
(2, '2023-12-15', 1, 4.5, 'Excellent technical leadership and mentoring', '2023 Annual'),
(3, '2023-12-15', 1, 4.2, 'Strong performance, good collaboration', '2023 Annual'),
(4, '2023-12-15', 1, 4.3, 'Great work on infrastructure improvements', '2023 Annual'),
(5, '2023-12-15', 1, 4.1, 'Solid QA practices, caught critical bugs', '2023 Annual'),

-- Sales reviews
(7, '2023-12-20', 6, 4.7, 'Exceeded quota by 35%, excellent client relationships', '2023 Annual'),
(8, '2023-12-20', 6, 4.0, 'Met targets, good team player', '2023 Annual'),
(9, '2023-12-20', 6, 3.8, 'Approaching targets, needs more follow-up', '2023 Annual'),
(10, '2023-12-20', 6, 4.6, 'Outstanding enterprise deals closed', '2023 Annual'),

-- Marketing reviews
(12, '2023-12-18', 11, 4.4, 'Effective campaign management', '2023 Annual'),
(13, '2023-12-18', 11, 4.3, 'Great content quality and consistency', '2023 Annual'),
(14, '2023-12-18', 11, 3.9, 'Good work, needs more initiative', '2023 Annual'),

-- Finance reviews
(19, '2023-12-22', 18, 4.6, 'Exceptional financial modeling', '2023 Annual'),
(20, '2023-12-22', 18, 4.1, 'Accurate and timely reporting', '2023 Annual'),
(21, '2023-12-22', 18, 4.0, 'Solid analytical skills', '2023 Annual'),

-- Product reviews
(23, '2023-12-19', 22, 4.5, 'Strong product vision and execution', '2023 Annual'),
(24, '2023-12-19', 22, 4.2, 'Good roadmap planning', '2023 Annual'),
(25, '2023-12-19', 22, 3.9, 'Shows promise, needs more experience', '2023 Annual'),

-- Support reviews
(27, '2023-12-21', 26, 4.3, 'Excellent team leadership', '2023 Annual'),
(28, '2023-12-21', 26, 4.1, 'Great customer satisfaction scores', '2023 Annual'),
(29, '2023-12-21', 26, 4.0, 'Responsive and helpful', '2023 Annual');

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count records in each table
SELECT 'locations' as table_name, COUNT(*) as record_count FROM locations
UNION ALL
SELECT 'departments', COUNT(*) FROM departments
UNION ALL
SELECT 'employees', COUNT(*) FROM employees
UNION ALL
SELECT 'salary_history', COUNT(*) FROM salary_history
UNION ALL
SELECT 'projects', COUNT(*) FROM projects
UNION ALL
SELECT 'project_assignments', COUNT(*) FROM project_assignments
UNION ALL
SELECT 'performance_reviews', COUNT(*) FROM performance_reviews;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================
