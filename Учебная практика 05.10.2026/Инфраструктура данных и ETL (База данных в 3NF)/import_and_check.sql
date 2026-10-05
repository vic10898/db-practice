-- =============================================================================
-- Практическая работа 05.10.2026
-- Скрипт проверки целостности и загрузки данных: import_and_check.sql
-- =============================================================================

-- Включение проверки внешних ключей
PRAGMA foreign_keys = ON;

-- 1. Первичное заполнение справочников типов продукции и материалов
INSERT OR IGNORE INTO product_types (product_type_id, type_name, coefficient) VALUES
(1, 'Паркетная доска', 4.34),
(2, 'Ламинат', 2.35),
(3, 'Массивная доска', 5.15),
(4, 'Пробковое покрытие', 1.50);

INSERT OR IGNORE INTO material_types (material_type_id, type_name, defect_rate) VALUES
(1, 'Тип материала 1 (Дубовый шпон)', 0.28),
(2, 'Тип материала 2 (Хвойная подложка)', 0.55),
(3, 'Тип материала 3 (Защитный лак)', 0.12),
(4, 'Тип материала 4 (Пробковая гранула)', 0.85);

-- 2. Проверочные запросы количества записей в таблицах
-- Ожидается:
-- partners: 5 записей
-- products: 3 записи
-- sales_history: 5 записей (1 запись с ID 1003 исключена из-за отсутствия партнера 999)

SELECT 'Количество партнеров:' AS metric, COUNT(*) AS count FROM partners;
SELECT 'Количество товаров:' AS metric, COUNT(*) AS count FROM products;
SELECT 'Количество записей продаж:' AS metric, COUNT(*) AS count FROM sales_history;

-- 3. Проверка на отсутствие лишних пробелов в текстовых полях
SELECT partner_id, partner_name, inn, email
FROM partners
WHERE partner_name != TRIM(partner_name)
   OR inn != TRIM(inn)
   OR email != TRIM(email);

-- 4. Проверка ссылочной целостности (поиск «висячих» внешних ключей)
SELECT sh.sale_id, sh.partner_id
FROM sales_history sh
LEFT JOIN partners p ON sh.partner_id = p.partner_id
WHERE p.partner_id IS NULL;

-- 5. Итоговый отчет по объемам продаж и агрегатам для каждого партнера
SELECT 
    p.partner_id,
    p.partner_type,
    p.partner_name,
    p.inn,
    p.email,
    COALESCE(SUM(sh.quantity), 0) AS total_quantity,
    COALESCE(SUM(sh.amount), 0.00) AS total_sales_amount
FROM partners p
LEFT JOIN sales_history sh ON p.partner_id = sh.partner_id
GROUP BY p.partner_id, p.partner_type, p.partner_name, p.inn, p.email
ORDER BY p.partner_id;
