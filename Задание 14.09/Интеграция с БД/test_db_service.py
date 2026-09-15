import unittest
import sqlite3
from db_service import get_partner_sales_volume, get_partner_with_discount, get_all_partners_with_discounts


def init_mock_db(connection):
    """Инициализация таблиц тестовой БД."""
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY,
            company_name TEXT NOT NULL,
            inn TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            contact_phone TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY,
            partner_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            delivery_date TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE VIEW IF NOT EXISTS sales_history AS
        SELECT id, partner_id, product_id, quantity, delivery_date
        FROM deliveries;
    """)

    cursor.execute("SELECT COUNT(*) FROM partners;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO partners (id, company_name, inn, email, contact_phone) VALUES
            (1, 'ООО "Логистик-Экспресс"', '7701234567', 'info@logex.ru', '+7 (999) 111-22-33'),
            (2, 'ИП Петров А.В.', '5001098765', 'petrov_delivery@mail.ru', NULL),
            (3, 'ТК "Быстрый Путь"', '7812345678', 'speedway@yandex.ru', '+78125554433'),
            (4, 'ООО "Новый Партнер"', '7709998877', 'new_partner@mail.ru', '+7 (999) 444-55-66');
        """)

        cursor.execute("""
            INSERT INTO deliveries (id, partner_id, product_id, quantity, delivery_date) VALUES
            (101, 1, 1, 50, '2026-03-01'),
            (102, 1, 3, 30, '2026-03-20'),
            (103, 2, 2, 15000, '2026-03-15'),
            (104, 3, 1, 40000, '2026-03-10'),
            (105, 3, 2, 25000, '2026-03-25');
        """)

        connection.commit()


class TestDatabaseIntegration(unittest.TestCase):
    """
    Набор тестов для проверки интеграции с базой данных,
    корректности агрегации продаж (SUM + LEFT JOIN) и расчета скидок.
    """

    @classmethod
    def setUpClass(cls):
        cls.connection = sqlite3.connect(":memory:")
        cls.connection.row_factory = sqlite3.Row
        init_mock_db(cls.connection)

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def test_get_partner_sales_volume_with_sales(self):
        """Проверка агрегации суммарного объема продаж партнера."""
        volume_1 = get_partner_sales_volume(1, self.connection)
        self.assertEqual(volume_1, 80)

        volume_2 = get_partner_sales_volume(2, self.connection)
        self.assertEqual(volume_2, 15000)

        volume_3 = get_partner_sales_volume(3, self.connection)
        self.assertEqual(volume_3, 65000)

    def test_get_partner_sales_volume_without_sales_left_join(self):
        """Проверка работы LEFT JOIN: у партнера 4 нет отгрузок в sales_history."""
        volume_4 = get_partner_sales_volume(4, self.connection)
        self.assertEqual(volume_4, 0)

    def test_partner_with_discount_calculation(self):
        """Проверка объединения запроса к БД с расчетом скидки."""
        partner_1 = get_partner_with_discount(1, self.connection)
        self.assertEqual(partner_1["discount_percent"], 0)

        partner_2 = get_partner_with_discount(2, self.connection)
        self.assertEqual(partner_2["discount_percent"], 5)

        partner_3 = get_partner_with_discount(3, self.connection)
        self.assertEqual(partner_3["discount_percent"], 10)

        partner_4 = get_partner_with_discount(4, self.connection)
        self.assertEqual(partner_4["discount_percent"], 0)

    def test_non_existent_partner_returns_none(self):
        """Проверка обработки несуществующего партнера."""
        partner = get_partner_with_discount(999, self.connection)
        self.assertIsNone(partner)

    def test_get_all_partners_with_discounts(self):
        """Проверка получения полного списка партнеров."""
        partners = get_all_partners_with_discounts(self.connection)
        self.assertEqual(len(partners), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
