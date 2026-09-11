-- =============================================================================
-- SQL-скрипт бизнес-запросов приложения (queries.sql)
-- Задание 4
-- =============================================================================

-- =============================================================================
-- ЗАПРОС 1: Список партнеров с сортировкой по названию и количеством их доставок
-- Используется LEFT JOIN и агрегатная функция COUNT.
-- Возвращает всех партнеров, отсортированных по алфавиту, и количество их отгрузок.
-- =============================================================================

SELECT 
    p.id AS partner_id,
    p.company_name,
    p.inn,
    p.email,
    p.contact_phone,
    COUNT(d.id) AS total_deliveries
FROM partners p
LEFT JOIN deliveries d ON p.id = d.partner_id
GROUP BY p.id, p.company_name, p.inn, p.email, p.contact_phone
ORDER BY p.company_name ASC;


-- =============================================================================
-- ЗАПРОС 2: Транзакционное добавление данных (BEGIN ... COMMIT)
-- Создание нового партнера и запись о его первой тестовой доставке 
-- в рамках одного единого транзакционного блока.
-- =============================================================================

BEGIN;

-- 2.1. Добавление нового партнера в таблицу partners
INSERT INTO partners (company_name, inn, email, contact_phone)
VALUES ('ООО "Логистика Будущего"', '7799887766', 'future_log@mail.ru', '+7 (999) 000-00-00');

-- 2.2. Запись о первой тестовой доставке для нового партнера
INSERT INTO deliveries (partner_id, product_id, quantity, delivery_date)
VALUES (
    (SELECT id FROM partners WHERE inn = '7799887766'),
    1,
    10,
    '2026-04-01'
);

COMMIT;


-- =============================================================================
-- ЗАПРОС 3: История реализации (детальная история отгрузок конкретного партнера)
-- Вывод истории отгрузок партнера за указанный период с расчетом итоговой суммы.
-- =============================================================================

SELECT 
    p.company_name AS partner_name,
    pr.product_name,
    d.delivery_date,
    d.quantity AS quantity_pcs,
    pr.base_price,
    (d.quantity * pr.base_price) AS total_amount
FROM deliveries d
JOIN partners p ON d.partner_id = p.id
JOIN products pr ON d.product_id = pr.id
WHERE d.partner_id = 1
  AND d.delivery_date BETWEEN '2026-03-01' AND '2026-03-31'
ORDER BY d.delivery_date ASC;
