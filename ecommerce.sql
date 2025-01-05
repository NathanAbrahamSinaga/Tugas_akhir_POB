CREATE DATABASE ecommerce;

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER NOT NULL,
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(200) NOT NULL,
    customer_email VARCHAR(200) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    price_pe

INSERT INTO products (name, description, price, stock) VALUES
('Laptop', 'Laptop dengan spesifikasi tinggi', 12000000.00, 10),
('Smartphone', 'Smartphone dengan kamera 48MP', 5000000.00, 20);

INSERT INTO orders (customer_name, customer_email, total_amount) VALUES
('John Doe', 'john.doe@example.com', 12000000.00),
('Jane Doe', 'jane.doe@example.com', 5000000.00);

INSERT INTO order_items (order_id, product_id, quantity, price_per_unit) VALUES
(1, 1, 1, 12000000.00),
(2, 2, 1, 5000000.00);

