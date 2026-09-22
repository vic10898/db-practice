import unittest
import tkinter as tk
from main_window import MainWindow
from partner_edit_window import PartnerEditWindow


class TestNavigation(unittest.TestCase):
    """
    Модульные тесты многооконной архитектуры и переходов между окнами.
    """

    def setUp(self):
        # Инициализируем главное окно в скрытом режиме для headless-проверок
        self.root = MainWindow()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_main_window_title(self):
        """Проверка заголовка главного окна реестра партнеров."""
        self.assertEqual(self.root.title(), "CRM: Реестр партнеров")

    def test_open_add_window_title(self):
        """Проверка заголовка окна при создании нового партнера."""
        edit_window = PartnerEditWindow(master=self.root, partner_id=None)
        self.assertEqual(edit_window.title(), "CRM: Карточка партнера [Создание]")
        edit_window.on_back_clicked()

    def test_open_edit_window_title(self):
        """Проверка заголовка окна при редактировании существующего партнера."""
        edit_window = PartnerEditWindow(master=self.root, partner_id=5)
        self.assertEqual(edit_window.title(), "CRM: Карточка партнера [Редактирование]")
        edit_window.on_back_clicked()

    def test_navigation_callback_on_back(self):
        """Проверка возврата управления и вызова callback при закрытии окна."""
        callback_called = False

        def on_close():
            nonlocal callback_called
            callback_called = True

        edit_window = PartnerEditWindow(master=self.root, partner_id=1, on_close_callback=on_close)
        edit_window.on_back_clicked()

        self.assertTrue(callback_called)
        self.assertFalse(edit_window.winfo_exists())


if __name__ == "__main__":
    unittest.main()
