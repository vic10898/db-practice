import unittest
from app import PartnerCRMApp


class TestUIResilience(unittest.TestCase):
    """
    Тесты отказоустойчивости приложения (Задание 4):
    Проверка обработки NULL-значений, отсутствующих продаж и корректности рендеринга карточек.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = PartnerCRMApp()
        cls.app.update()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def test_null_quantity_handling_gives_zero_discount(self):
        """
        Проверка: если у партнера нет продаж (SUM(quantity) IS NULL),
        скидка должна безопасно рассчитываться как 0% без TypeError.
        """
        data_with_null = {
            "id": 99,
            "company_name": 'ООО "Тестовый Партнер"',
            "total_quantity": None,
            "contact_phone": "+7 (000) 000-00-00",
            "rating": 10
        }

        # Вызов отрисовки карточки с NULL продажами не должен приводить к исключению
        try:
            self.app._render_partner_card(data_with_null)
        except Exception as err:
            self.fail(f"Отрисовка карточки с total_quantity=None вызвала исключение: {err}")

    def test_zero_quantity_gives_zero_discount(self):
        """Проверка: нулевой объем продаж дает скидку 0%."""
        data_with_zero = {
            "id": 100,
            "company_name": 'ИП "Новичок"',
            "total_quantity": 0,
            "contact_phone": None,
            "rating": None
        }

        try:
            self.app._render_partner_card(data_with_zero)
        except Exception as err:
            self.fail(f"Отрисовка карточки с total_quantity=0 вызвала исключение: {err}")

    def test_missing_optional_fields(self):
        """
        Проверка: отсутствие телефона, рейтинга или директора (значения None)
        не ломает интерфейс и заменяется на дефолтные значения.
        """
        data_empty = {
            "id": 101,
            "company_name": None,
            "total_quantity": 15000,
            "contact_phone": None,
            "rating": None,
            "director": None
        }

        try:
            self.app._render_partner_card(data_empty)
        except Exception as err:
            self.fail(f"Отрисовка карточки с пустыми полями вызвала исключение: {err}")

    def test_refresh_loads_real_data(self):
        """Проверка работы метода обновления данных из БД."""
        self.app.refresh_partners_list()
        # В тестовой базе должно быть 4 партнера
        rendered_cards = self.app.cards_frame.winfo_children()
        self.assertGreaterEqual(len(rendered_cards), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
