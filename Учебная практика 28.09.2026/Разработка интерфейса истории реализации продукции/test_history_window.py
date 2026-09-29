import os
import unittest
import sqlite3

from db_manager import DatabaseManager


class TestPartnerHistory(unittest.TestCase):
    """
    Тестирование подсистемы отображения истории реализации продукции.
    Проверяет корректность SQL JOIN, структуру возвращаемых данных
    и форматирование дат.
    """

    def setUp(self):
        self.test_db_path = ":memory:"
        self.db = DatabaseManager(db_path=self.test_db_path)

    def test_sql_join_returns_correct_fields(self):
        """Проверка, что запрос возвращает обязательные поля: наименование, количество, дата."""
        history = self.db.get_partner_sales_history(1)
        self.assertGreater(len(history), 0)

        first_record = history[0]
        self.assertIn("product_name", first_record)
        self.assertIn("quantity", first_record)
        self.assertIn("delivery_date", first_record)

        self.assertIsInstance(first_record["product_name"], str)
        self.assertIsInstance(first_record["quantity"], int)
        self.assertIsInstance(first_record["delivery_date"], str)

    def test_partner_sales_history_empty_for_new_partner(self):
        """Проверка возврата пустого списка отгрузок для нового контрагента без продаж."""
        new_partner_id = self.db.add_partner({
            "company_name": "ООО Ромашка",
            "partner_type": "ООО",
            "rating": 5,
            "address": "г. Тверь",
            "director": "Иванов И.И.",
            "contact_phone": "+7 (999) 000-00-00",
            "email": "romashka@example.com"
        })
        history = self.db.get_partner_sales_history(new_partner_id)
        self.assertEqual(history, [])

    def test_correct_product_names_after_join(self):
        """Проверка точности связывания по внешнему ключу product_id."""
        history = self.db.get_partner_sales_history(1)
        # У партнера 1 в seed-данных есть отгрузка "Паркет Дуб Натуральный 14 мм"
        product_names = [item["product_name"] for item in history]
        self.assertIn("Паркет Дуб Натуральный 14 мм", product_names)

    def test_date_ordering(self):
        """Проверка сортировки отгрузок по дате от новых к старым."""
        history = self.db.get_partner_sales_history(1)
        dates = [item["delivery_date"] for item in history]
        self.assertEqual(dates, sorted(dates, reverse=True))


if __name__ == "__main__":
    unittest.main()
