import unittest
import os
import tempfile
from db_manager import DatabaseManager, IntegrityViolationError, PartnerNotFoundError


class TestDatabaseCRUD(unittest.TestCase):
    """
    Модульные тесты выполнения CRUD-операций и ссылочной целостности базы данных.
    """

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db = DatabaseManager(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_add_partner_success(self):
        """Проверка успешного добавления нового партнера (INSERT)."""
        new_partner = {
            "company_name": "ООО АльфаТрейд",
            "partner_type": "ООО",
            "rating": 15,
            "address": "г. Москва, ул. Тверская, 1",
            "director": "Смирнов С.С.",
            "contact_phone": "+7 (495) 123-45-67",
            "email": "alfa_trade@test.ru"
        }
        partner_id = self.db.add_partner(new_partner)
        self.assertIsInstance(partner_id, int)
        self.assertGreater(partner_id, 0)

        # Проверка чтения добавленной записи
        fetched = self.db.get_partner_by_id(partner_id)
        self.assertEqual(fetched["company_name"], "ООО АльфаТрейд")
        self.assertEqual(fetched["partner_type"], "ООО")
        self.assertEqual(fetched["rating"], 15)
        self.assertEqual(fetched["email"], "alfa_trade@test.ru")

    def test_update_partner_success(self):
        """Проверка корректного обновления существующего партнера (UPDATE)."""
        update_data = {
            "company_name": "Логистик-Экспресс Модерн",
            "partner_type": "ЗАО",
            "rating": 25,
            "address": "г. Москва, пр-т Мира, 100",
            "director": "Иванов И.И.",
            "contact_phone": "+7 (999) 000-11-22",
            "email": "info_new@logex.ru"
        }
        self.db.update_partner(1, update_data)

        updated = self.db.get_partner_by_id(1)
        self.assertEqual(updated["company_name"], "Логистик-Экспресс Модерн")
        self.assertEqual(updated["partner_type"], "ЗАО")
        self.assertEqual(updated["rating"], 25)
        self.assertEqual(updated["email"], "info_new@logex.ru")

    def test_update_non_existing_partner_raises_error(self):
        """Проверка обработки запроса на изменение несуществующей записи."""
        with self.assertRaises(PartnerNotFoundError):
            self.db.update_partner(9999, {
                "company_name": "Тест",
                "partner_type": "ООО",
                "rating": 0,
                "address": "",
                "director": "",
                "contact_phone": "",
                "email": "test@none.ru"
            })

    def test_duplicate_email_integrity_error(self):
        """Проверка защиты ссылочной и семантической целостности по уникальному email."""
        duplicate = {
            "company_name": "Дубликат",
            "partner_type": "ООО",
            "rating": 5,
            "address": "",
            "director": "",
            "contact_phone": "",
            "email": "info@logex.ru"  # Email уже занят партнером с ID 1
        }
        with self.assertRaises(IntegrityViolationError):
            self.db.add_partner(duplicate)

    def test_sales_aggregation_and_discount(self):
        """Проверка расчета скидки для существующих и новых партнеров."""
        partners = self.db.get_all_partners()
        partner_1 = next(p for p in partners if p["id"] == 1)
        self.assertEqual(partner_1["total_sales"], 80)
        self.assertEqual(partner_1["discount"], 0)

        partner_3 = next(p for p in partners if p["id"] == 3)
        self.assertEqual(partner_3["total_sales"], 65000)
        self.assertEqual(partner_3["discount"], 10)


if __name__ == "__main__":
    unittest.main()
