-- ============================================================================
-- RETAIL STORE DATABASE SCHEMA
-- E-commerce style: categories, suppliers, products, stores, customers,
-- orders, order_items — designed for JOIN and aggregation testing.
-- ============================================================================

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS stores CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- ============================================================================
-- TABLE: categories
-- ============================================================================
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- ============================================================================
-- TABLE: suppliers
-- ============================================================================
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    company_name VARCHAR(150) NOT NULL,
    country VARCHAR(100) NOT NULL,
    phone VARCHAR(30)
);

-- ============================================================================
-- TABLE: products
-- ============================================================================
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    sku VARCHAR(40) UNIQUE NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    supplier_id INTEGER NOT NULL REFERENCES suppliers(supplier_id)
);

-- ============================================================================
-- TABLE: stores
-- ============================================================================
CREATE TABLE stores (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    opened_date DATE NOT NULL
);

-- ============================================================================
-- TABLE: customers
-- ============================================================================
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    city VARCHAR(100) NOT NULL,
    customer_since DATE NOT NULL
);

-- ============================================================================
-- TABLE: orders
-- ============================================================================
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    store_id INTEGER NOT NULL REFERENCES stores(store_id),
    order_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Processing',
    shipping_cost DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (shipping_cost >= 0),
    CONSTRAINT chk_order_status CHECK (status IN ('Completed', 'Shipped', 'Processing', 'Cancelled'))
);

-- ============================================================================
-- TABLE: order_items
-- ============================================================================
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    line_total DECIMAL(12, 2) NOT NULL CHECK (line_total >= 0)
);

-- ============================================================================
-- INSERT: categories
-- ============================================================================
INSERT INTO categories (category_name, description) VALUES
('Electronics', 'Phones, laptops, accessories'),
('Apparel', 'Clothing and shoes'),
('Home & Kitchen', 'Cookware and decor'),
('Sports', 'Equipment and outdoor'),
('Books', 'Print and educational'),
('Beauty', 'Skincare and cosmetics');

-- ============================================================================
-- INSERT: suppliers
-- ============================================================================
INSERT INTO suppliers (company_name, country, phone) VALUES
('Pacific Components Ltd', 'Japan', '+81-3-5550-1001'),
('Nordic Trade AB', 'Sweden', '+46-8-555-0200'),
('Chenzhou Manufacturing', 'China', '+86-574-5550-3300'),
('Americana Supply Co', 'USA', '+1-415-555-0140'),
('EuroHome Distributors', 'Germany', '+49-30-5550-4400'),
('Andean Textiles SA', 'Peru', '+51-1-5550-5500'),
('Global Beauty Group', 'France', '+33-1-5550-6600'),
('UK Print Partners', 'United Kingdom', '+44-20-5550-7700');

-- ============================================================================
-- INSERT: products (category_id 1-6, supplier_id 1-8)
-- ============================================================================
INSERT INTO products (product_name, sku, unit_price, stock_quantity, category_id, supplier_id) VALUES
('Wireless Earbuds Pro', 'EL-BUD-001', 79.99, 120, 1, 1),
('USB-C Hub 7-in-1', 'EL-HUB-002', 45.50, 85, 1, 1),
('Laptop Stand Aluminum', 'EL-STD-003', 34.00, 200, 1, 3),
('Cotton Crew Tee', 'AP-TEE-101', 19.99, 300, 2, 6),
('Running Shoes Lite', 'AP-SHO-102', 89.00, 75, 2, 6),
('Wool Scarf', 'AP-SCF-103', 29.50, 150, 2, 4),
('Stainless Kettle 1.7L', 'HK-KTL-201', 42.00, 60, 3, 5),
('Ceramic Dinner Set', 'HK-DNR-202', 115.00, 40, 3, 5),
('Yoga Mat 6mm', 'SP-YGA-301', 35.00, 90, 4, 4),
('Trail Backpack 28L', 'SP-BPK-302', 72.50, 55, 4, 4),
('SQL for Beginners', 'BK-SQL-401', 24.99, 200, 5, 8),
('Data Science Handbook', 'BK-DS-402', 39.99, 140, 5, 8),
('Classic Novel Collection', 'BK-NVL-403', 18.00, 95, 5, 8),
('Moisturizing Cream 50ml', 'BY-CRM-501', 22.00, 180, 6, 7),
('Vitamin C Serum', 'BY-SRM-502', 31.50, 110, 6, 7),
('Bluetooth Speaker Mini', 'EL-SPK-004', 55.00, 95, 1, 3),
('Desk Lamp LED', 'HK-LMP-203', 48.00, 70, 3, 5),
('Basketball Official', 'SP-BBL-303', 28.00, 100, 4, 4),
('Denim Jacket', 'AP-JKT-104', 64.00, 45, 2, 6),
('Cookbook Mediterranean', 'BK-CK-404', 27.50, 80, 5, 8),
('Lip Balm Set', 'BY-LIP-503', 12.99, 250, 6, 7),
('Gaming Mouse', 'EL-MSE-005', 49.99, 130, 1, 1);

-- ============================================================================
-- INSERT: stores
-- ============================================================================
INSERT INTO stores (store_name, city, opened_date) VALUES
('Downtown Flagship', 'Chicago', '2019-03-15'),
('West Mall Kiosk', 'Austin', '2020-06-01'),
('Harbor View Outlet', 'Seattle', '2018-11-20'),
('Metro Express', 'Boston', '2021-01-10'),
('Lakeside Superstore', 'Toronto', '2017-09-05');

-- ============================================================================
-- INSERT: customers
-- ============================================================================
INSERT INTO customers (first_name, last_name, email, city, customer_since) VALUES
('Emma', 'Nguyen', 'emma.nguyen@example.com', 'Chicago', '2021-02-10'),
('Liam', 'Patel', 'liam.patel@example.com', 'Austin', '2020-08-22'),
('Olivia', 'Chen', 'olivia.chen@example.com', 'Seattle', '2022-01-05'),
('Noah', 'Garcia', 'noah.garcia@example.com', 'Boston', '2019-11-30'),
('Ava', 'Kim', 'ava.kim@example.com', 'Toronto', '2023-03-18'),
('Ethan', 'Brown', 'ethan.brown@example.com', 'Chicago', '2022-07-14'),
('Sophia', 'Martinez', 'sophia.martinez@example.com', 'Austin', '2021-05-09'),
('Mason', 'Lee', 'mason.lee@example.com', 'Seattle', '2020-12-01'),
('Isabella', 'Wang', 'isabella.wang@example.com', 'Boston', '2023-08-20'),
('James', 'Wilson', 'james.wilson@example.com', 'Toronto', '2019-04-25'),
('Mia', 'Taylor', 'mia.taylor@example.com', 'Chicago', '2024-01-12'),
('Benjamin', 'Anderson', 'benjamin.anderson@example.com', 'Austin', '2022-09-03'),
('Charlotte', 'Thomas', 'charlotte.thomas@example.com', 'Seattle', '2021-10-28'),
('Lucas', 'Jackson', 'lucas.jackson@example.com', 'Boston', '2020-03-15'),
('Amelia', 'White', 'amelia.white@example.com', 'Toronto', '2022-06-07'),
('Henry', 'Harris', 'henry.harris@example.com', 'Chicago', '2023-02-22'),
('Harper', 'Martin', 'harper.martin@example.com', 'Austin', '2019-09-11'),
('Alexander', 'Clark', 'alexander.clark@example.com', 'Seattle', '2024-04-01'),
('Evelyn', 'Lewis', 'evelyn.lewis@example.com', 'Boston', '2021-12-19'),
('Daniel', 'Walker', 'daniel.walker@example.com', 'Toronto', '2020-07-08'),
('Abigail', 'Hall', 'abigail.hall@example.com', 'Chicago', '2023-05-30'),
('Matthew', 'Allen', 'matthew.allen@example.com', 'Austin', '2022-11-14'),
('Ella', 'Young', 'ella.young@example.com', 'Seattle', '2018-08-09'),
('Jackson', 'King', 'jackson.king@example.com', 'Boston', '2023-10-02');

-- ============================================================================
-- INSERT: orders
-- ============================================================================
INSERT INTO orders (customer_id, store_id, order_date, status, shipping_cost) VALUES
(1, 1, '2025-11-02', 'Completed', 5.99),
(2, 2, '2025-11-05', 'Shipped', 4.50),
(3, 3, '2025-11-08', 'Completed', 6.00),
(4, 4, '2025-11-10', 'Processing', 3.99),
(5, 5, '2025-11-12', 'Completed', 7.50),
(6, 1, '2025-11-14', 'Cancelled', 0.00),
(7, 2, '2025-11-15', 'Shipped', 4.50),
(8, 3, '2025-11-18', 'Completed', 6.00),
(9, 4, '2025-11-20', 'Completed', 3.99),
(10, 5, '2025-11-22', 'Shipped', 7.50),
(1, 2, '2025-12-01', 'Completed', 4.50),
(11, 1, '2025-12-03', 'Processing', 5.99),
(12, 3, '2025-12-05', 'Completed', 6.00),
(13, 4, '2025-12-07', 'Completed', 3.99),
(14, 5, '2025-12-09', 'Shipped', 7.50),
(15, 1, '2025-12-11', 'Completed', 5.99),
(16, 2, '2025-12-13', 'Completed', 4.50),
(17, 3, '2025-12-15', 'Cancelled', 0.00),
(18, 4, '2025-12-17', 'Shipped', 3.99),
(19, 5, '2025-12-19', 'Completed', 7.50),
(20, 1, '2026-01-05', 'Completed', 5.99),
(21, 2, '2026-01-08', 'Shipped', 4.50),
(22, 3, '2026-01-10', 'Completed', 6.00),
(23, 4, '2026-01-12', 'Processing', 3.99),
(24, 5, '2026-01-14', 'Completed', 7.50),
(3, 1, '2026-01-16', 'Completed', 5.99),
(8, 2, '2026-01-18', 'Shipped', 4.50),
(14, 3, '2026-01-20', 'Completed', 6.00);

-- ============================================================================
-- INSERT: order_items (line_total = illustrative snapshot totals)
-- ============================================================================
INSERT INTO order_items (order_id, product_id, quantity, line_total) VALUES
(1, 1, 1, 79.99),
(1, 14, 2, 44.00),
(2, 4, 3, 59.97),
(2, 9, 1, 35.00),
(3, 11, 2, 49.98),
(3, 12, 1, 39.99),
(4, 7, 1, 42.00),
(5, 2, 1, 45.50),
(5, 16, 1, 55.00),
(6, 5, 1, 89.00),
(7, 10, 1, 72.50),
(7, 18, 2, 56.00),
(8, 1, 2, 159.98),
(9, 20, 4, 51.96),
(10, 6, 2, 59.00),
(11, 3, 1, 34.00),
(11, 21, 1, 49.99),
(12, 8, 1, 115.00),
(13, 13, 1, 18.00),
(13, 19, 1, 64.00),
(14, 15, 1, 31.50),
(15, 17, 1, 48.00),
(16, 4, 2, 39.98),
(17, 22, 1, 12.99),
(18, 1, 1, 79.99),
(19, 5, 1, 89.00),
(20, 11, 1, 24.99),
(21, 9, 2, 70.00),
(22, 2, 2, 91.00),
(23, 7, 1, 42.00),
(24, 14, 1, 22.00),
(25, 10, 1, 72.50),
(26, 12, 1, 39.99),
(26, 20, 1, 27.50),
(27, 6, 1, 29.50),
(28, 16, 1, 55.00),
(28, 21, 2, 25.98),
(5, 22, 1, 49.99),
(12, 14, 1, 22.00),
(20, 18, 1, 28.00),
(22, 4, 1, 19.99);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_store ON orders(store_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_customers_city ON customers(city);

-- ============================================================================
-- PRIVILEGES (local / classroom demo)
-- Objects are owned by whoever runs this script (often a superuser). If your
-- app or DB explorer connects as another role (e.g. hari), that role needs SELECT.
-- PUBLIC keeps demo friction low; tighten in production.
-- ============================================================================
GRANT USAGE ON SCHEMA public TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO PUBLIC;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO PUBLIC;

-- ============================================================================
-- VERIFICATION
-- ============================================================================
SELECT 'categories' AS table_name, COUNT(*) AS record_count FROM categories
UNION ALL SELECT 'suppliers', COUNT(*) FROM suppliers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'stores', COUNT(*) FROM stores
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items;
