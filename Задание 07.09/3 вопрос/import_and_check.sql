-- =============================================================================
-- SQL-скрипт импорта подготовленных данных и проверки (Задание 3)
-- =============================================================================

-- 1. Импорт данных в таблицу партнеров (partners)
INSERT INTO partners (id, company_name, inn, email, contact_phone) VALUES
(1, 'ООО "Логистик-Экспресс"', '7701234567', 'info@logex.ru', '+7 (999) 111-22-33'),
(2, 'ИП Петров А.В.', '5001098765', 'petrov_delivery@mail.ru', NULL),
(3, 'ТК "Быстрый Путь"', '7812345678', 'speedway@yandex.ru', '+78125554433');

-- Примечание: Для выполнения импорта из файла через команды PostgreSQL COPY:
-- COPY partners(id, company_name, inn, email, contact_phone)
-- FROM '/path/to/cleaned_partners.csv' WITH (FORMAT csv, HEADER true);


-- 2. Импорт данных в таблицу продуктов (products)
INSERT INTO products (id, product_name, base_price) VALUES
(1, 'Стиральный порошок "Альфа"', 500.00),
(2, 'Мыло жидкое "Стандарт"', 90.00),
(3, 'Кондиционер для белья', 350.00);

-- Вариант COPY:
-- COPY products(id, product_name, base_price)
-- FROM '/path/to/cleaned_products.csv' WITH (FORMAT csv, HEADER true);


-- 3. Импорт данных в таблицу поставок (deliveries)
INSERT INTO deliveries (id, partner_id, product_id, quantity, delivery_date) VALUES
(101, 1, 1, 50, '2026-03-01'),
(102, 2, 2, 200, '2026-03-15'), -- Исправлен формат даты (с 15.03.2026 на 2026-03-15)
(103, 1, 3, 30, '2026-03-20'),
(105, 3, 2, 150, '2026-03-25');  -- Запись 104 с partner_id=4 исключена (партнер отсутствует в БД)

-- Вариант COPY:
-- COPY deliveries(id, partner_id, product_id, quantity, delivery_date)
-- FROM '/path/to/cleaned_deliveries.csv' WITH (FORMAT csv, HEADER true);


-- =============================================================================
-- ПРОВЕРОЧНЫЕ ЗАПРОСЫ (SELECT COUNT(*))
-- =============================================================================

SELECT COUNT(*) AS total_partners FROM partners;
-- Ожидаемый результат: 3

SELECT COUNT(*) AS total_products FROM products;
-- Ожидаемый результат: 3

SELECT COUNT(*) AS total_deliveries FROM deliveries;
-- Ожидаемый результат: 4
