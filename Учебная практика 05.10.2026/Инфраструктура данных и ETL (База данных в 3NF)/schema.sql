-- =============================================================================
-- Практическая работа 05.10.2026
-- Проектирование реляционной схемы базы данных (3NF)
-- Скрипт DDL: schema.sql
-- =============================================================================

-- Включение поддержки внешних ключей (для SQLite)
PRAGMA foreign_keys = ON;

-- Удаление существующих таблиц в правильном порядке зависимостей
DROP TABLE IF EXISTS sales_history;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS product_types;
DROP TABLE IF EXISTS material_types;
DROP TABLE IF EXISTS partners;

-- 1. Таблица партнеров (partners)
-- Обеспечивает хранение реквизитов контрагентов.
-- Ограничения: ИНН и Email уникальны и обязательны для заполнения.
CREATE TABLE partners (
    partner_id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_name VARCHAR(255) NOT NULL,
    partner_type VARCHAR(50) NOT NULL DEFAULT 'ООО',
    rating INTEGER NOT NULL DEFAULT 0 CHECK (rating >= 0),
    address VARCHAR(255),
    director VARCHAR(255),
    phone VARCHAR(50),
    inn VARCHAR(12) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE
);

-- 2. Таблица справочника типов продукции (product_types)
-- Нормализация 3NF: вынесение коэффициента типа в отдельный справочник
CREATE TABLE product_types (
    product_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name VARCHAR(255) NOT NULL UNIQUE,
    coefficient REAL NOT NULL CHECK (coefficient > 0)
);

-- 3. Таблица справочника типов материалов (material_types)
-- Нормализация 3NF: процент брака сырья
CREATE TABLE material_types (
    material_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name VARCHAR(255) NOT NULL UNIQUE,
    defect_rate REAL NOT NULL CHECK (defect_rate >= 0)
);

-- 4. Таблица номенклатуры продукции (products)
-- Цены хранятся с фиксированной точностью DECIMAL(10, 2)
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name VARCHAR(255) NOT NULL,
    product_type_id INTEGER,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    CONSTRAINT fk_products_product_types
        FOREIGN KEY (product_type_id)
        REFERENCES product_types (product_type_id)
        ON DELETE SET NULL
);

-- 5. Таблица истории реализации (sales_history)
-- Обеспечивает ссылочную целостность через внешние ключи:
-- при удалении партнера каскадно удаляются продажи,
-- удаление товара запрещено при наличии истории продаж (RESTRICT).
CREATE TABLE sales_history (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    sale_date DATE NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    amount DECIMAL(12, 2) NOT NULL CHECK (amount >= 0),
    CONSTRAINT fk_sales_partners
        FOREIGN KEY (partner_id)
        REFERENCES partners (partner_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_sales_products
        FOREIGN KEY (product_id)
        REFERENCES products (product_id)
        ON DELETE RESTRICT
);

-- Создание индексов для ускорения поиска и агрегаций по внешним ключам
CREATE INDEX idx_sales_partner ON sales_history (partner_id);
CREATE INDEX idx_sales_product ON sales_history (product_id);
CREATE INDEX idx_sales_date ON sales_history (sale_date);
