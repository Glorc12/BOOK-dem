-- SQLite schema for the tkinter + PIL bookstore solution.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    full_name TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS manufacturers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS pickup_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    price NUMERIC NOT NULL,
    discount INTEGER NOT NULL DEFAULT 0,
    stock_qty INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT '',
    photo_path TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    manufacturer_id INTEGER NOT NULL,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    FOREIGN KEY(supplier_id) REFERENCES suppliers(id) ON DELETE RESTRICT,
    FOREIGN KEY(manufacturer_id) REFERENCES manufacturers(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number INTEGER NOT NULL UNIQUE,
    status TEXT NOT NULL,
    order_date TEXT,
    delivery_date TEXT,
    receive_code INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    pickup_point_id INTEGER NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY(pickup_point_id) REFERENCES pickup_points(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    UNIQUE(order_id, product_id),
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT
);
