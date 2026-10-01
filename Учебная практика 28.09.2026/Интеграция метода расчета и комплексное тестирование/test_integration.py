import unittest
import tkinter as tk
from unittest.mock import patch

from db_manager import DatabaseManager
from material_calculator import calculate_material_requirement
from material_calculator_window import MaterialCalculatorWindow


class TestIntegrationMaterialCalculator(unittest.TestCase):
    """
    Комплексные тесты интеграции метода расчета материалов с интерфейсом:
    проверка вывода результатов, обработки некорректных данных и устойчивости к сбоям.
    """

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def setUp(self):
        self.db = DatabaseManager(db_path=":memory:")
        self.window = MaterialCalculatorWindow(master=self.root, db_manager=self.db)

    def tearDown(self):
        try:
            self.window.destroy()
        except Exception:
            pass

    def test_window_initialization_loads_references(self):
        """Проверка наполнения выпадающих списков из справочников БД."""
        self.assertGreater(len(self.window.combo_product_type["values"]), 0)
        self.assertGreater(len(self.window.combo_material_type["values"]), 0)
        self.assertIn("Паркетная доска", self.window.combo_product_type["values"][0])

    def test_successful_calculation_updates_ui(self):
        """Проверка успешного вывода результата расчета на экран формы."""
        self.window.combo_product_type.current(0)  # ID 1 (коэффициент 4.34)
        self.window.combo_material_type.current(0)  # ID 1 (брак 0.28%)

        self.window.entry_quantity.delete(0, tk.END)
        self.window.entry_quantity.insert(0, "100")

        self.window.entry_param1.delete(0, tk.END)
        self.window.entry_param1.insert(0, "1.5")

        self.window.entry_param2.delete(0, tk.END)
        self.window.entry_param2.insert(0, "2.0")

        self.window.perform_calculation()

        # 1.5 * 2.0 * 4.34 * 100 * 1.0028 = 1305.64 -> ceil -> 1306
        self.assertEqual(self.window.result_value_lbl.cget("text"), "1 306 ед.")
        self.assertEqual(self.window.result_value_lbl.cget("fg"), "#059669")

    @patch("dialogs.AppDialogs.show_error")
    def test_negative_dimension_handles_gracefully(self, mock_show_error):
        """Проверка, что отрицательный параметр не валит UI, а выводит ошибку."""
        self.window.combo_product_type.current(0)
        self.window.combo_material_type.current(0)

        self.window.entry_quantity.insert(0, "10")
        self.window.entry_param1.insert(0, "-1.5")
        self.window.entry_param2.insert(0, "2.0")

        self.window.perform_calculation()

        # Приложение не упало, вызван диалог ошибки и выставлен статус ошибки
        mock_show_error.assert_called_once()
        self.assertEqual(self.window.result_value_lbl.cget("text"), "Ошибка данных")

    @patch("dialogs.AppDialogs.show_error")
    def test_non_numeric_input_handles_gracefully(self, mock_show_error):
        """Проверка обработки некорректных строковых символов вместо чисел."""
        self.window.entry_quantity.insert(0, "abc")
        self.window.entry_param1.insert(0, "1.0")
        self.window.entry_param2.insert(0, "2.0")

        self.window.perform_calculation()

        mock_show_error.assert_called_once()
        self.assertEqual(self.window.result_value_lbl.cget("text"), "Ошибка данных")

    @patch("dialogs.AppDialogs.show_error")
    def test_zero_quantity_handles_gracefully(self, mock_show_error):
        """Проверка обработки нулевого объема партии."""
        self.window.combo_product_type.current(0)
        self.window.combo_material_type.current(0)

        self.window.entry_quantity.insert(0, "0")
        self.window.entry_param1.insert(0, "1.0")
        self.window.entry_param2.insert(0, "1.0")

        self.window.perform_calculation()

        mock_show_error.assert_called_once()
        self.assertEqual(self.window.result_value_lbl.cget("text"), "Ошибка данных")

    def test_reset_form_clears_fields(self):
        """Проверка очистки формы по кнопке «Очистить»."""
        self.window.entry_quantity.insert(0, "50")
        self.window.entry_param1.insert(0, "2.0")
        self.window.entry_param2.insert(0, "3.0")

        self.window.reset_form()

        self.assertEqual(self.window.entry_quantity.get(), "")
        self.assertEqual(self.window.entry_param1.get(), "")
        self.assertEqual(self.window.entry_param2.get(), "")
        self.assertEqual(self.window.result_value_lbl.cget("text"), "—")


if __name__ == "__main__":
    unittest.main()
