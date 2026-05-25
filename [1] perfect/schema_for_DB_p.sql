DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    login VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(64) NOT NULL,
    full_name VARCHAR(150) NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    article VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL DEFAULT 'Без категории',
    description TEXT NOT NULL DEFAULT '',
    manufacturer VARCHAR(150) NOT NULL DEFAULT 'Не указан',
    supplier VARCHAR(150) NOT NULL DEFAULT 'Не указан',
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    discount INTEGER NOT NULL DEFAULT 0 CHECK (discount >= 0 AND discount <= 100),
    unit VARCHAR(30) NOT NULL DEFAULT 'шт',
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    image_path TEXT NOT NULL DEFAULT ''
);

INSERT INTO roles (name) VALUES
('guest'),
('client'),
('manager'),
('admin');
