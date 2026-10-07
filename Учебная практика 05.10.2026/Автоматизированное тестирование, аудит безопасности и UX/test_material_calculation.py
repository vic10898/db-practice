# -*- coding: utf-8 -*-
import unittest
import math
from db_manager import DatabaseManager


class TestMaterialCalculationCases(unittest.TestCase):
    """
    Комплекс обязательных модульных тестов метода расчета расхода сырья
    (не менее 5 тест-кейсов согласно техническому заданию).
    """

    @classmethod
    def setUpClass(cls):
        # Инициализация тестовой базы данных в памяти
        cls.db = DatabaseManager(":memory:")

    def test_case_1_base_calculation(self):
        """Тест-кейс 1: Проверка базового расчета расхода сырья по формуле ТЗ."""
        # Параметры:
        # count = 100
        # product_type_id = 1 ("Паркетная доска", коэффициент = 4.34)
        # material_type_id = 1 ("Тип материала 1", процент брака = 0.28%)
        # param1 = 2.0, param2 = 1.5
        # Расчет:
        # unit = 2.0 * 1.5 * 4.34 = 13.02
        # total = 100 * 13.02 * (1 + 0.28 / 100) = 1302 * 1.0028 = 1305.6456 -> math.ceil -> 1306
        res = self.db.calculate_material(
            count=100,
            product_type_id=1,
            material_type_id=1,
            param1=2.0,
            param2=1.5
        )
        self.assertEqual(res, 1306)

    def test_case_2_strict_ceil_rounding(self):
        """Тест-кейс 2: Проверка математического округления строго вверх (math.ceil)."""
        # Параметры подобраны так, чтобы дробная часть была минимальной:
        # count = 1, param1 = 1.0, param2 = 1.0
        # product_type_id = 4 ("Пробковое покрытие", коэффициент = 1.50)
        # material_type_id = 3 ("Защитный лак", процент брака = 0.12%)
        # raw = 1 * 1.0 * 1.0 * 1.50 * (1 + 0.12 / 100) = 1.5018 -> ceil -> 2
        res = self.db.calculate_material(
            count=1,
            product_type_id=4,
            material_type_id=3,
            param1=1.0,
            param2=1.0
        )
        self.assertEqual(res, 2)

    def test_case_3_nonexistent_product_type_id(self):
        """Тест-кейс 3: Обработка несуществующего ID типа продукции (возврат -1)."""
        res = self.db.calculate_material(
            count=50,
            product_type_id=99999,  # тип продукции отсутствует в БД
            material_type_id=1,
            param1=2.0,
            param2=1.0
        )
        self.assertEqual(res, -1)

    def test_case_4_nonexistent_material_type_id(self):
        """Тест-кейс 4: Обработка несуществующего ID типа материала (возврат -1)."""
        res = self.db.calculate_material(
            count=50,
            product_type_id=1,
            material_type_id=77777,  # тип материала отсутствует в БД
            param1=2.0,
            param2=1.0
        )
        self.assertEqual(res, -1)

    def test_case_5_negative_parameters(self):
        """Тест-кейс 5: Обработка отрицательных параметров (строгий возврат -1 вместо падения)."""
        # Отрицательное количество продукции
        self.assertEqual(
            self.db.calculate_material(-10, 1, 1, 2.0, 1.5),
            -1
        )
        # Отрицательный параметр 1
        self.assertEqual(
            self.db.calculate_material(10, 1, 1, -2.5, 1.5),
            -1
        )
        # Отрицательный параметр 2
        self.assertEqual(
            self.db.calculate_material(10, 1, 1, 2.0, -1.5),
            -1
        )

    def test_case_6_zero_quantity(self):
        """Дополнительный кейс: нулевой объем производства (расход 0)."""
        res = self.db.calculate_material(0, 1, 1, 2.0, 1.5)
        self.assertEqual(res, 0)


if __name__ == "__main__":
    unittest.main()
