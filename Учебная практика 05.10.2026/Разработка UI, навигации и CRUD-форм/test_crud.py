# -*- coding: utf-8 -*-
import unittest
from db_manager import DatabaseManager, DatabaseIntegrityError, PartnerNotFoundError
from validators import validate_partner_form_data, ValidationError


class TestCrudOperations(unittest.TestCase):
    """Модульные тесты CRUD-операций и синхронизации данных."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_get_all_partners(self):
        """Проверка получения списка партнеров с расчетом скидок."""
        partners = self.db.get_all_partners()
        self.assertGreaterEqual(len(partners), 5)
        # Проверка наличия обязательных полей
        first = partners[0]
        self.assertIn("partner_id", first)
        self.assertIn("partner_name", first)
        self.assertIn("discount", first)
        self.assertIn("rating", first)

    def test_add_partner_success(self):
        """Проверка успешного добавления нового контрагента."""
        data = {
            "partner_name": "ООО «Тест Продакшн»",
            "partner_type": "ООО",
            "rating": 15,
            "inn": "7799112233",
            "email": "test_prod@example.com",
            "phone": "+7 (999) 111-22-33",
            "director": "Иванов И.И.",
            "address": "г. Москва"
        }
        new_id = self.db.add_partner(data)
        self.assertIsNotNone(new_id)

        p = self.db.get_partner_by_id(new_id)
        self.assertEqual(p["partner_name"], "ООО «Тест Продакшн»")
        self.assertEqual(p["rating"], 15)
        self.assertEqual(p["email"], "test_prod@example.com")

    def test_update_partner_success(self):
        """Проверка обновления реквизитов партнера."""
        data = {
            "partner_name": "ООО «Вектор Обновленный»",
            "partner_type": "ООО",
            "rating": 25,
            "inn": "7701234567",
            "email": "vector_new@mail.ru",
            "phone": "+7 999 123-45-67",
            "director": "Новый Директор",
            "address": "г. Санкт-Петербург"
        }
        self.db.update_partner(1, data)
        p = self.db.get_partner_by_id(1)
        self.assertEqual(p["partner_name"], "ООО «Вектор Обновленный»")
        self.assertEqual(p["rating"], 25)
        self.assertEqual(p["email"], "vector_new@mail.ru")

    def test_delete_partner_cascade(self):
        """Проверка удаления партнера и каскадного удаления связанных продаж."""
        # У партнера 1 есть продажи (sale_id 1001)
        sales_before = self.db.get_partner_sales_history(1)
        self.assertGreater(len(sales_before), 0)

        self.db.delete_partner(1)

        # Партнер больше не должен находиться
        with self.assertRaises(PartnerNotFoundError):
            self.db.get_partner_by_id(1)

        # Продажи удалились каскадно
        sales_after = self.db.get_partner_sales_history(1)
        self.assertEqual(len(sales_after), 0)

    def test_unique_email_constraint(self):
        """Проверка срабатывания ограничения уникальности Email."""
        data = {
            "partner_name": "Дубликат Email",
            "partner_type": "ООО",
            "rating": 5,
            "inn": "1112223334",
            "email": "vector@mail.ru"  # уже занят партнером 1
        }
        with self.assertRaises(DatabaseIntegrityError):
            self.db.add_partner(data)

    def test_validation_empty_name(self):
        """Проверка валидации: пустое наименование вызывает ValidationError."""
        bad_data = {
            "partner_name": "",
            "email": "valid@email.com",
            "rating": "10"
        }
        with self.assertRaises(ValidationError):
            validate_partner_form_data(bad_data)

    def test_validation_negative_rating(self):
        """Проверка валидации: отрицательный рейтинг вызывает ValidationError."""
        bad_data = {
            "partner_name": "Компания",
            "email": "valid@email.com",
            "rating": "-5"
        }
        with self.assertRaises(ValidationError):
            validate_partner_form_data(bad_data)


if __name__ == "__main__":
    unittest.main()
