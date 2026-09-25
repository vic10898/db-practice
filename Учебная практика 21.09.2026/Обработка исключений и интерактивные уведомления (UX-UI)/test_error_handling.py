import unittest
import os
import tempfile
import tkinter as tk
from validators import validate_partner_form_data, ValidationError
from db_manager import DatabaseManager, DatabaseIntegrityError, PartnerNotFoundError
from partner_edit_window import PartnerEditWindow


class TestErrorHandlingAndValidation(unittest.TestCase):
    """
    Модульные тесты обработки исключений, валидации полей и логики предупреждений.
    """

    def test_valid_data_passes(self):
        """Проверка успешной валидации корректно заполненных данных."""
        raw_data = {
            "company_name": "ООО Рога и Копыта",
            "partner_type": "ООО",
            "rating": "10",
            "address": "г. Москва",
            "director": "Остап Бендер",
            "contact_phone": "+7 999 111 22 33",
            "email": "bender@horns-hooves.ru"
        }
        cleaned = validate_partner_form_data(raw_data)
        self.assertEqual(cleaned["company_name"], "ООО Рога и Копыта")
        self.assertEqual(cleaned["rating"], 10)
        self.assertEqual(cleaned["email"], "bender@horns-hooves.ru")

    def test_empty_company_name_raises_error(self):
        """Проверка требования обязательного заполнения наименования."""
        raw_data = {
            "company_name": "   ",
            "partner_type": "ООО",
            "rating": "5",
            "email": "valid@mail.ru"
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_partner_form_data(raw_data)
        self.assertIn("«Наименование» не может быть пустым", str(ctx.exception))
        self.assertEqual(ctx.exception.field_name, "company_name")

    def test_empty_email_raises_error(self):
        """Проверка требования обязательного заполнения email."""
        raw_data = {
            "company_name": "ООО Прогресс",
            "partner_type": "ООО",
            "rating": "5",
            "email": ""
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_partner_form_data(raw_data)
        self.assertIn("«Email» обязательно", str(ctx.exception))
        self.assertEqual(ctx.exception.field_name, "email")

    def test_invalid_email_format_raises_error(self):
        """Проверка валидации синтаксиса адреса электронной почты."""
        raw_data = {
            "company_name": "ООО Прогресс",
            "partner_type": "ООО",
            "rating": "5",
            "email": "invalid_email_at_domain"
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_partner_form_data(raw_data)
        self.assertIn("некорректный формат email", str(ctx.exception))

    def test_negative_rating_raises_error(self):
        """Проверка запрета отрицательного рейтинга."""
        raw_data = {
            "company_name": "ООО Прогресс",
            "partner_type": "ООО",
            "rating": "-5",
            "email": "info@progress.ru"
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_partner_form_data(raw_data)
        self.assertIn("Рейтинг должен быть целым числом от 0", str(ctx.exception))
        self.assertEqual(ctx.exception.field_name, "rating")

    def test_non_integer_rating_raises_error(self):
        """Проверка запрета нечислового или дробного рейтинга."""
        for invalid_val in ["12.5", "10,5", "десять", "15!"]:
            raw_data = {
                "company_name": "ООО Прогресс",
                "partner_type": "ООО",
                "rating": invalid_val,
                "email": "info@progress.ru"
            }
            with self.assertRaises(ValidationError) as ctx:
                validate_partner_form_data(raw_data)
            self.assertIn("Рейтинг должен быть целым числом от 0", str(ctx.exception))

    def test_dirty_form_tracking(self):
        """Проверка отслеживания изменений пользователем для предупреждения при закрытии."""
        root = tk.Tk()
        root.withdraw()
        try:
            form = PartnerEditWindow(master=root)
            self.assertFalse(form.is_dirty())

            # Модифицируем поле ввода
            form.entry_name.insert(0, "Новая компания")
            self.assertTrue(form.is_dirty())
            form.on_force_close()
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
