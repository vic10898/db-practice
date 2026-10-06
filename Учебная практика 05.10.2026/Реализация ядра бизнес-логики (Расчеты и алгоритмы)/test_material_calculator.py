# -*- coding: utf-8 -*-
import unittest
import math
from db_manager import DatabaseManager
from material_calculator import calculate_material_requirement


class TestMaterialCalculator(unittest.TestCase):
    """Набор тестов для алгоритма расчета расхода сырья."""

    @classmethod
    def setUpClass(cls):
        # Использование общей тестовой базы данных в памяти
        cls.db = DatabaseManager(":memory:")

    def test_basic_calculation(self):
        """1. Базовый расчет: корректные параметры, проверка формулы."""
        # product_type 1: коэффициент 4.34
        # material_type 1: брак 0.28%
        # count = 100, param1 = 2.0, param2 = 1.5
        # unit = 2.0 * 1.5 * 4.34 = 13.02
        # total = 100 * 13.02 * (1 + 0.0028) = 1302 * 1.0028 = 1305.6456 -> ceil = 1306
        res = calculate_material_requirement(100, 1, 1, 2.0, 1.5, self.db)
        self.assertEqual(res, 1306)

    def test_ceil_rounding(self):
        """2. Проверка округления строго вверх (math.ceil)."""
        # count = 1, param1 = 1.0, param2 = 1.0
        # product_type 4: 1.50
        # material_type 3: 0.12%
        # raw = 1.50 * 1.0012 = 1.5018 -> ceil = 2
        res = calculate_material_requirement(1, 4, 3, 1.0, 1.0, self.db)
        self.assertEqual(res, 2)

    def test_nonexistent_product_type(self):
        """3. Несуществующий ID типа продукции: возврат -1."""
        res = calculate_material_requirement(50, 9999, 1, 1.0, 1.0, self.db)
        self.assertEqual(res, -1)

    def test_nonexistent_material_type(self):
        """4. Несуществующий ID типа материала: возврат -1."""
        res = calculate_material_requirement(50, 1, 8888, 1.0, 1.0, self.db)
        self.assertEqual(res, -1)

    def test_negative_parameters(self):
        """5. Отрицательные параметры: возврат -1."""
        self.assertEqual(calculate_material_requirement(-10, 1, 1, 1.0, 1.0, self.db), -1)
        self.assertEqual(calculate_material_requirement(10, 1, 1, -1.5, 1.0, self.db), -1)
        self.assertEqual(calculate_material_requirement(10, 1, 1, 1.0, -2.0, self.db), -1)

    def test_zero_count(self):
        """Нулевое количество продукции: расход 0."""
        res = calculate_material_requirement(0, 1, 1, 2.0, 1.5, self.db)
        self.assertEqual(res, 0)


if __name__ == "__main__":
    unittest.main()
