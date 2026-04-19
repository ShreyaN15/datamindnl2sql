-- ============================================================================
-- LIBRARY MANAGEMENT DATABASE SCHEMA
-- A comprehensive library management system with branches, members, authors, 
-- books, loans, and reviews
-- ============================================================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS loans CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS members CASCADE;
DROP TABLE IF EXISTS authors CASCADE;
DROP TABLE IF EXISTS branches CASCADE;

-- ============================================================================
-- TABLE: branches
-- Library branch locations
-- ============================================================================
CREATE TABLE branches (
    branch_id SERIAL PRIMARY KEY,
    branch_name VARCHAR(150) NOT NULL UNIQUE,
    city VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    manager_id INTEGER  -- Will be set after members are created
);

-- ============================================================================
-- TABLE: members
-- Library members/patrons
-- ============================================================================
CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    join_date DATE NOT NULL,
    membership_type VARCHAR(50) NOT NULL,  -- 'Standard', 'Premium', 'Student'
    branch_id INTEGER REFERENCES branches(branch_id),
    CONSTRAINT fk_members_branch
        FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

-- ============================================================================
-- TABLE: authors
-- Book authors
-- ============================================================================
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    nationality VARCHAR(100),
    birth_date DATE
);

-- ============================================================================
-- TABLE: books
-- Books in the library
-- ============================================================================
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    genre VARCHAR(100),
    published_year INTEGER,
    total_copies INTEGER NOT NULL DEFAULT 1,
    available_copies INTEGER NOT NULL DEFAULT 1,
    author_id INTEGER REFERENCES authors(author_id),
    branch_id INTEGER REFERENCES branches(branch_id),
    CONSTRAINT fk_books_author
        FOREIGN KEY (author_id) REFERENCES authors(author_id),
    CONSTRAINT fk_books_branch
        FOREIGN KEY (branch_id) REFERENCES branches(branch_id),
    CONSTRAINT check_available_copies
        CHECK (available_copies >= 0 AND available_copies <= total_copies)
);

-- ============================================================================
-- TABLE: loans
-- Book loan records
-- ============================================================================
CREATE TABLE loans (
    loan_id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(book_id),
    member_id INTEGER REFERENCES members(member_id),
    loan_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE,
    status VARCHAR(20) DEFAULT 'Active',  -- 'Active', 'Returned', 'Overdue'
    CONSTRAINT fk_loans_book
        FOREIGN KEY (book_id) REFERENCES books(book_id),
    CONSTRAINT fk_loans_member
        FOREIGN KEY (member_id) REFERENCES members(member_id)
);

-- ============================================================================
-- TABLE: reviews
-- Book reviews by members
-- ============================================================================
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(book_id),
    member_id INTEGER REFERENCES members(member_id),
    rating DECIMAL(2, 1) CHECK (rating >= 1.0 AND rating <= 5.0),
    review_text TEXT,
    review_date DATE NOT NULL,
    CONSTRAINT fk_reviews_book
        FOREIGN KEY (book_id) REFERENCES books(book_id),
    CONSTRAINT fk_reviews_member
        FOREIGN KEY (member_id) REFERENCES members(member_id),
    UNIQUE(book_id, member_id)
);

-- ============================================================================
-- Add foreign key for manager_id after members table is populated
-- ============================================================================
ALTER TABLE branches
ADD CONSTRAINT fk_branches_manager
    FOREIGN KEY (manager_id) REFERENCES members(member_id);

-- ============================================================================
-- INSERT DATA: branches
-- ============================================================================
INSERT INTO branches (branch_name, city, phone, manager_id) VALUES
('Downtown Library', 'San Francisco', '555-0101', NULL),
('Westside Branch', 'San Francisco', '555-0102', NULL),
('Midtown Library', 'New York', '555-0201', NULL),
('Upper West Library', 'New York', '555-0202', NULL),
('Tech District Branch', 'Austin', '555-0301', NULL),
('University Library', 'Boston', '555-0401', NULL),
('Waterfront Branch', 'Seattle', '555-0501', NULL);

-- ============================================================================
-- INSERT DATA: members
-- ============================================================================
INSERT INTO members (first_name, last_name, email, join_date, membership_type, branch_id) VALUES
-- Downtown Library
('Alice', 'Johnson', 'alice.johnson@mail.com', '2022-01-10', 'Premium', 1),
('Robert', 'Smith', 'robert.smith@mail.com', '2021-06-15', 'Standard', 1),
('Margaret', 'Williams', 'margaret.williams@mail.com', '2023-03-20', 'Standard', 1),
('James', 'Brown', 'james.brown@mail.com', '2022-09-05', 'Student', 1),
('Patricia', 'Jones', 'patricia.jones@mail.com', '2020-11-12', 'Premium', 1),

-- Westside Branch
('Michael', 'Garcia', 'michael.garcia@mail.com', '2022-04-18', 'Standard', 2),
('Linda', 'Martinez', 'linda.martinez@mail.com', '2023-01-25', 'Premium', 2),
('David', 'Rodriguez', 'david.rodriguez@mail.com', '2021-08-30', 'Standard', 2),
('Barbara', 'Lee', 'barbara.lee@mail.com', '2022-12-10', 'Student', 2),

-- Midtown Library
('Richard', 'Davis', 'richard.davis@mail.com', '2020-02-14', 'Premium', 3),
('Susan', 'Miller', 'susan.miller@mail.com', '2022-05-22', 'Standard', 3),
('Joseph', 'Wilson', 'joseph.wilson@mail.com', '2023-07-10', 'Standard', 3),
('Jessica', 'Anderson', 'jessica.anderson@mail.com', '2021-10-17', 'Premium', 3),

-- Upper West Library
('Thomas', 'Taylor', 'thomas.taylor@mail.com', '2022-03-08', 'Standard', 4),
('Mary', 'Thomas', 'mary.thomas@mail.com', '2023-02-14', 'Premium', 4),
('Charles', 'Jackson', 'charles.jackson@mail.com', '2020-09-21', 'Student', 4),

-- Tech District Branch
('Christopher', 'White', 'christopher.white@mail.com', '2022-06-30', 'Premium', 5),
('Nancy', 'Harris', 'nancy.harris@mail.com', '2021-11-05', 'Standard', 5),
('Daniel', 'Clark', 'daniel.clark@mail.com', '2023-04-12', 'Standard', 5),

-- University Library
('Matthew', 'Lewis', 'matthew.lewis@mail.com', '2022-08-20', 'Student', 6),
('Karen', 'Walker', 'karen.walker@mail.com', '2021-12-03', 'Premium', 6),
('Mark', 'Hall', 'mark.hall@mail.com', '2023-05-15', 'Standard', 6),

-- Waterfront Branch
('Donald', 'Young', 'donald.young@mail.com', '2022-02-10', 'Premium', 7),
('Sandra', 'Allen', 'sandra.allen@mail.com', '2021-07-28', 'Standard', 7),
('Steven', 'King', 'steven.king@mail.com', '2023-01-30', 'Student', 7);

-- Update branch managers
UPDATE branches SET manager_id = 1 WHERE branch_name = 'Downtown Library';
UPDATE branches SET manager_id = 6 WHERE branch_name = 'Westside Branch';
UPDATE branches SET manager_id = 10 WHERE branch_name = 'Midtown Library';
UPDATE branches SET manager_id = 15 WHERE branch_name = 'Upper West Library';
UPDATE branches SET manager_id = 19 WHERE branch_name = 'Tech District Branch';
UPDATE branches SET manager_id = 22 WHERE branch_name = 'University Library';
UPDATE branches SET manager_id = 25 WHERE branch_name = 'Waterfront Branch';

-- ============================================================================
-- INSERT DATA: authors
-- ============================================================================
INSERT INTO authors (first_name, last_name, nationality, birth_date) VALUES
('George', 'Orwell', 'British', '1903-06-25'),
('Jane', 'Austen', 'British', '1775-12-16'),
('Mark', 'Twain', 'American', '1835-11-30'),
('Charlotte', 'Bronte', 'British', '1818-04-21'),
('F. Scott', 'Fitzgerald', 'American', '1896-09-24'),
('J.R.R.', 'Tolkien', 'British', '1892-01-03'),
('Agatha', 'Christie', 'British', '1890-01-15'),
('Isaac', 'Asimov', 'American-Russian', '1920-01-02'),
('Stephen', 'King', 'American', '1947-09-21'),
('J.K.', 'Rowling', 'British', '1965-07-31'),
('Paulo', 'Coelho', 'Brazilian', '1947-08-24'),
('Dan', 'Brown', 'American', '1964-06-22');

-- ============================================================================
-- INSERT DATA: books
-- ============================================================================
INSERT INTO books (title, isbn, genre, published_year, total_copies, available_copies, author_id, branch_id) VALUES
('1984', '978-0451524935', 'Dystopian', 1949, 5, 3, 1, 1),
('Pride and Prejudice', '978-0141439518', 'Romance', 1813, 4, 2, 2, 1),
('The Adventures of Tom Sawyer', '978-0486400778', 'Fiction', 1876, 3, 1, 3, 1),
('Jane Eyre', '978-0141441146', 'Gothic', 1847, 3, 2, 4, 2),
('The Great Gatsby', '978-0743273565', 'Fiction', 1925, 6, 4, 5, 2),
('The Hobbit', '978-0547928227', 'Fantasy', 1937, 4, 3, 6, 3),
('Murder on the Orient Express', '978-0062693556', 'Mystery', 1934, 3, 1, 7, 3),
('Foundation', '978-0553293357', 'Science Fiction', 1951, 2, 1, 8, 3),
('The Shining', '978-0385333312', 'Horror', 1977, 3, 2, 9, 4),
('Harry Potter and the Sorcerers Stone', '978-0439708180', 'Fantasy', 1997, 7, 5, 10, 4),
('The Alchemist', '978-0061122415', 'Fiction', 1988, 4, 2, 11, 5),
('The Da Vinci Code', '978-0307474278', 'Mystery', 2003, 5, 3, 12, 5),
('To Kill a Mockingbird', '978-0061120084', 'Fiction', 1960, 4, 1, 3, 6),
('Wuthering Heights', '978-0141439556', 'Gothic', 1847, 2, 1, 4, 6),
('The Catcher in the Rye', '978-0316769174', 'Fiction', 1951, 3, 2, 1, 7),
('Emma', '978-0141439587', 'Romance', 1815, 3, 2, 2, 7);

-- ============================================================================
-- INSERT DATA: loans
-- ============================================================================
INSERT INTO loans (book_id, member_id, loan_date, due_date, return_date, status) VALUES
-- Active loans
(1, 2, '2026-04-01', '2026-04-15', NULL, 'Active'),
(2, 3, '2026-04-05', '2026-04-19', NULL, 'Active'),
(5, 4, '2026-03-28', '2026-04-11', NULL, 'Overdue'),
(6, 5, '2026-04-03', '2026-04-17', NULL, 'Active'),
(9, 7, '2026-04-02', '2026-04-16', NULL, 'Active'),
(10, 8, '2026-03-30', '2026-04-13', NULL, 'Overdue'),
(12, 11, '2026-04-04', '2026-04-18', NULL, 'Active'),

-- Returned loans
(1, 1, '2026-03-15', '2026-03-29', '2026-03-28', 'Returned'),
(3, 2, '2026-03-10', '2026-03-24', '2026-03-22', 'Returned'),
(4, 3, '2026-03-20', '2026-04-03', '2026-03-31', 'Returned'),
(6, 4, '2026-02-15', '2026-03-01', '2026-02-28', 'Returned'),
(7, 6, '2026-03-25', '2026-04-08', '2026-04-07', 'Returned'),
(8, 9, '2026-02-20', '2026-03-06', '2026-03-05', 'Returned'),
(11, 10, '2026-03-12', '2026-03-26', '2026-03-24', 'Returned'),
(2, 12, '2026-03-18', '2026-04-01', '2026-03-31', 'Returned'),
(5, 13, '2026-02-25', '2026-03-11', '2026-03-10', 'Returned');

-- ============================================================================
-- INSERT DATA: reviews
-- ============================================================================
INSERT INTO reviews (book_id, member_id, rating, review_text, review_date) VALUES
(1, 2, 5.0, 'Thought-provoking and deeply unsettling. A true masterpiece.', '2026-03-28'),
(2, 3, 4.5, 'Classic romance with witty dialogue. Wonderful read.', '2026-03-22'),
(5, 4, 4.0, 'Beautiful prose and fascinating characters. Highly recommended.', '2026-03-31'),
(6, 5, 5.0, 'Epic fantasy adventure. Simply unforgettable.', '2026-02-28'),
(7, 6, 4.5, 'Clever mystery with great pacing. Could not put it down.', '2026-04-07'),
(8, 9, 4.8, 'Incredible science fiction concepts. Mind-bending ideas.', '2026-03-05'),
(10, 8, 5.0, 'Magical and captivating. Perfect for all ages.', '2026-04-07'),
(11, 10, 4.3, 'Inspirational story about self-discovery. Very meaningful.', '2026-03-24'),
(12, 12, 4.5, 'Intriguing mystery with a fast-paced plot.', '2026-03-31'),
(3, 1, 4.0, 'Charming adventure story with timeless appeal.', '2026-03-28'),
(4, 13, 4.7, 'Dark and atmospheric. Excellent gothic novel.', '2026-03-10');

-- ============================================================================
-- CREATE INDEXES for better query performance
-- ============================================================================
CREATE INDEX idx_members_branch ON members(branch_id);
CREATE INDEX idx_members_email ON members(email);
CREATE INDEX idx_members_join_date ON members(join_date);
CREATE INDEX idx_authors_birth_date ON authors(birth_date);
CREATE INDEX idx_books_author ON books(author_id);
CREATE INDEX idx_books_branch ON books(branch_id);
CREATE INDEX idx_books_genre ON books(genre);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_loans_book ON loans(book_id);
CREATE INDEX idx_loans_member ON loans(member_id);
CREATE INDEX idx_loans_loan_date ON loans(loan_date);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE INDEX idx_reviews_member ON reviews(member_id);
CREATE INDEX idx_reviews_date ON reviews(review_date);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count records in each table
SELECT 'branches' as table_name, COUNT(*) as record_count FROM branches
UNION ALL
SELECT 'members', COUNT(*) FROM members
UNION ALL
SELECT 'authors', COUNT(*) FROM authors
UNION ALL
SELECT 'books', COUNT(*) FROM books
UNION ALL
SELECT 'loans', COUNT(*) FROM loans
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================
