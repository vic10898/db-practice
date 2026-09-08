-- =============================================================================
-- SQL-скрипт развертывания структуры базы данных (schema.sql)
-- =============================================================================

-- 1. Удаление таблиц с учетом порядка зависимостей
-- Сначала удаляем дочернюю таблицу (deliveries), содержащую внешние ключи,
-- а затем родительские таблицы (products, partners).
DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS partners;

-- 2. Создание таблицы партнеров (partners)
CREATE TABLE partners (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    inn VARCHAR(12) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    contact_phone VARCHAR(20)
);

-- 3. Создание таблицы продуктов (products)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL
);

-- 4. Создание таблицы поставок (deliveries)
CREATE TABLE deliveries (
    id SERIAL PRIMARY KEY,
    partner_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    delivery_date DATE NOT NULL,
    
    -- Внешние ключи (FOREIGN KEY) с явным указанием действий при удалении
    CONSTRAINT fk_deliveries_partners 
        FOREIGN KEY (partner_id) 
        REFERENCES partners (id) 
        ON DELETE CASCADE,
        
    CONSTRAINT fk_deliveries_products 
        FOREIGN KEY (product_id) 
        REFERENCES products (id) 
        ON DELETE RESTRICT
);
