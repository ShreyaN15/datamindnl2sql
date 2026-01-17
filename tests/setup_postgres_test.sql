-- Create test database for schema inference testing
-- This will create a realistic e-commerce schema with foreign keys

-- Create test database
DROP DATABASE IF EXISTS datamind_test;
CREATE DATABASE datamind_test;

-- Connect to the test database
\c datamind_test;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Create products table with FK to categories
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table with FK to users
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create order_items table with FKs to orders and products
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Create reviews table with FKs to users and products
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (username, email) VALUES
    ('john_doe', 'john@example.com'),
    ('jane_smith', 'jane@example.com'),
    ('bob_wilson', 'bob@example.com');

INSERT INTO categories (name, description) VALUES
    ('Electronics', 'Electronic devices and gadgets'),
    ('Books', 'Physical and digital books'),
    ('Clothing', 'Apparel and fashion items');

INSERT INTO products (name, category_id, price, stock) VALUES
    ('Laptop', 1, 999.99, 10),
    ('Smartphone', 1, 699.99, 25),
    ('Python Programming Book', 2, 49.99, 50),
    ('T-Shirt', 3, 19.99, 100);

INSERT INTO orders (user_id, total_amount, status) VALUES
    (1, 1049.98, 'completed'),
    (2, 699.99, 'pending'),
    (3, 69.98, 'completed');

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
    (1, 1, 1, 999.99),
    (1, 2, 1, 49.99),
    (2, 2, 1, 699.99),
    (3, 3, 1, 49.99),
    (3, 4, 1, 19.99);

INSERT INTO reviews (user_id, product_id, rating, comment) VALUES
    (1, 1, 5, 'Excellent laptop, very fast!'),
    (2, 2, 4, 'Good phone, battery life could be better'),
    (3, 3, 5, 'Great book for learning Python!');

-- Display schema summary
SELECT 
    'Tables created' as status,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE';

SELECT 
    'Foreign keys created' as status,
    COUNT(*) as count
FROM information_schema.table_constraints 
WHERE constraint_type = 'FOREIGN KEY'
  AND table_schema = 'public';
