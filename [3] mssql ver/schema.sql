IF OBJECT_ID('products', 'U') IS NOT NULL DROP TABLE products;
IF OBJECT_ID('users', 'U') IS NOT NULL DROP TABLE users;
IF OBJECT_ID('roles', 'U') IS NOT NULL DROP TABLE roles;

CREATE TABLE roles (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    full_name NVARCHAR(150) NOT NULL,
    login NVARCHAR(100) NOT NULL UNIQUE,
    password NVARCHAR(100) NOT NULL,
    role_id INT NOT NULL REFERENCES roles(id)
);

CREATE TABLE products (
    id_p INT IDENTITY(1,1) PRIMARY KEY,
    article_num NVARCHAR(6) NOT NULL UNIQUE,
    product NVARCHAR(100) NOT NULL,
    unit NVARCHAR(10) NOT NULL DEFAULT N'шт',
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    supplier NVARCHAR(100) NOT NULL,
    creator NVARCHAR(100) NOT NULL,
    category NVARCHAR(100) NOT NULL,
    discount INT NOT NULL DEFAULT 0 CHECK (discount >= 0 AND discount <= 100),
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    description NVARCHAR(300) NOT NULL,
    photo NVARCHAR(300) NOT NULL DEFAULT N''
);
