-- Mini Company Demo Database (2 tables)
-- Purpose: quick unseen-schema NL2SQL demo with simple JOINs + aggregations

DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS teams;

CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL
);

CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role_title VARCHAR(100) NOT NULL,
    monthly_salary NUMERIC(10,2) NOT NULL,
    join_date DATE NOT NULL,
    team_id INT NOT NULL,
    CONSTRAINT fk_members_team
        FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

INSERT INTO teams (team_name, city) VALUES
('Platform', 'San Francisco'),
('Growth', 'New York'),
('Support', 'Austin');

INSERT INTO members (first_name, last_name, role_title, monthly_salary, join_date, team_id) VALUES
('Ava', 'Reed', 'Backend Engineer', 8500.00, '2023-02-10', 1),
('Noah', 'Kim', 'DevOps Engineer', 9000.00, '2022-11-04', 1),
('Mia', 'Patel', 'Product Analyst', 7000.00, '2024-01-15', 2),
('Liam', 'Diaz', 'Growth Marketer', 6800.00, '2023-08-21', 2),
('Emma', 'Stone', 'Support Specialist', 5200.00, '2024-03-01', 3),
('Ethan', 'Cole', 'Support Lead', 6100.00, '2021-07-18', 3),
('Sofia', 'Ng', 'Data Engineer', 8800.00, '2022-05-30', 1),
('Lucas', 'Gray', 'Account Manager', 7300.00, '2020-09-12', 2);
