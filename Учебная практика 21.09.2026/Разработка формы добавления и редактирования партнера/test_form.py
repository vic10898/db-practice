import unittest
import tkinter as tk
from partner_edit_window import PartnerEditWindow, PlaceholderEntry


class TestPartnerForm(unittest.TestCase):
    """
    Модульные тесты интерфейса карточки добавления и редактирования партнера.
    """

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_combobox_partner_types(self):
        """Проверка списка допустимых типов организаций (ЗАО, ООО, ИП и др.)."""
        form = PartnerEditWindow(master=self.root)
        expected_types = ("ЗАО", "ООО", "ИП", "ПАО", "ОАО")
        self.assertEqual(tuple(form.combo_type["values"]), expected_types)
        self.assertEqual(form.combo_type.get(), "ООО")
        form.on_back_clicked()

    def test_form_fields_initial_state(self):
        """Проверка наличия и начального состояния полей формы."""
        form = PartnerEditWindow(master=self.root)
        self.assertEqual(form.entry_name.get(), "")
        self.assertEqual(form.entry_rating.get(), "0")
        self.assertEqual(form.entry_address.get(), "")
        self.assertEqual(form.entry_director.get(), "")
        # Для полей с плейсхолдером get_real_value() возвращает пустую строку
        self.assertEqual(form.entry_phone.get_real_value(), "")
        self.assertEqual(form.entry_email.get_real_value(), "")
        form.on_back_clicked()

    def test_populate_fields_in_edit_mode(self):
        """Проверка автоматической подгрузки данных партнера в режиме редактирования."""
        test_data = {
            "id": 10,
            "company_name": "ООО МегаТрейд",
            "partner_type": "ЗАО",
            "rating": 15,
            "address": "г. Екатеринбург, ул. Мира, 5",
            "director": "Кузнецов К.К.",
            "contact_phone": "+7 (343) 123-45-67",
            "email": "info@megatrade.ru"
        }
        form = PartnerEditWindow(master=self.root, partner_id=10, partner_data=test_data)

        self.assertEqual(form.entry_name.get(), "ООО МегаТрейд")
        self.assertEqual(form.combo_type.get(), "ЗАО")
        self.assertEqual(form.entry_rating.get(), "15")
        self.assertEqual(form.entry_address.get(), "г. Екатеринбург, ул. Мира, 5")
        self.assertEqual(form.entry_director.get(), "Кузнецов К.К.")
        self.assertEqual(form.entry_phone.get_real_value(), "+7 (343) 123-45-67")
        self.assertEqual(form.entry_email.get_real_value(), "info@megatrade.ru")

        collected = form.get_form_data()
        self.assertEqual(collected["id"], 10)
        self.assertEqual(collected["company_name"], "ООО МегаТрейд")
        self.assertEqual(collected["partner_type"], "ЗАО")
        self.assertEqual(collected["rating"], "15")
        form.on_back_clicked()


if __name__ == "__main__":
    unittest.main()
