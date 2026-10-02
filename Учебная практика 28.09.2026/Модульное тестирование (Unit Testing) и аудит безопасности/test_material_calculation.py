import unittest
import math

from db_manager import DatabaseManager
from material_calculator import calculate_material_requirement


class TestMaterialCalculationMethod(unittest.TestCase):
    """
    Набор модульных тестов для метода расчета материалов calculate_material_requirement.
    Включает 5 обязательных тест-кейсов по ТЗ и расширенные проверки типов данных.
    """

    def setUp(self):
        # Использование изолированной базы данных в оперативной памяти
        self.db = DatabaseManager(db_path=":memory:")

    def test_01_standard_calculation(self):
        """
        Тест 1 (Стандартный):
        Проверка обычного корректного расчета с известным результатом.
        Исходные параметры:
        — product_type_id = 1 (Паркетная доска, коэффициент 4.34)
        — material_type_id = 1 (Дубовый шпон, процент брака 0.28%)
        — param_1 = 1.5 м, param_2 = 2.0 м
        — quantity = 100 шт.
        Математика:
        Базовый расход на 1 ед. = 1.5 * 2.0 * 4.34 = 13.02
        Общий чистый расход = 13.02 * 100 = 1302.0
        С учетом брака = 1302.0 * (1 + 0.28 / 100) = 1305.6456
        math.ceil(1305.6456) = 1306 ед.
        """
        result = calculate_material_requirement(
            product_type_id=1,
            material_type_id=1,
            quantity=100,
            param_1=1.5,
            param_2=2.0,
            db_manager=self.db
        )
        self.assertEqual(result, 1306)

    def test_02_rounding_strictly_up(self):
        """
        Тест 2 (Округление):
        Проверка, что дробный результат округляется строго в большую сторону (вверх)
        до целого числа (math.ceil).
        Параметры:
        — product_type_id = 2 (Ламинат, коэффициент 2.35)
        — material_type_id = 3 (Защитный лак, процент брака 0.12%)
        — param_1 = 1.0, param_2 = 1.0, quantity = 1
        Чистый расход = 1.0 * 1.0 * 2.35 * 1 = 2.35
        С учетом брака = 2.35 * (1 + 0.12 / 100) = 2.35282
        Округление вверх = 3 (не 2).
        """
        result = calculate_material_requirement(
            product_type_id=2,
            material_type_id=3,
            quantity=1,
            param_1=1.0,
            param_2=1.0,
            db_manager=self.db
        )
        self.assertEqual(result, 3)

        # Дополнительная проверка минимальной дробной части
        # Например, 100.0001 -> должно округлиться до 101
        # product_type_id = 4 (Пробковое покрытие, коэф 1.50)
        # material_type_id = 1 (брак 0.28%)
        # param_1 = 0.5, param_2 = 1.0, quantity = 1 -> 0.5 * 1.50 * 1.0028 = 0.7521 -> ceil -> 1
        res_fractional = calculate_material_requirement(
            product_type_id=4,
            material_type_id=1,
            quantity=1,
            param_1=0.5,
            param_2=1.0,
            db_manager=self.db
        )
        self.assertEqual(res_fractional, 1)

    def test_03_nonexistent_type_ids_returns_minus_one(self):
        """
        Тест 3 (Несуществующий тип):
        Проверка возврата -1 при передаче некорректных ID типов продукции/материала.
        """
        # Несуществующий product_type_id = 99999
        res_prod_err = calculate_material_requirement(
            product_type_id=99999,
            material_type_id=1,
            quantity=10,
            param_1=2.0,
            param_2=2.0,
            db_manager=self.db
        )
        self.assertEqual(res_prod_err, -1)

        # Несуществующий material_type_id = -5
        res_mat_err = calculate_material_requirement(
            product_type_id=1,
            material_type_id=-5,
            quantity=10,
            param_1=2.0,
            param_2=2.0,
            db_manager=self.db
        )
        self.assertEqual(res_mat_err, -1)

    def test_04_negative_or_zero_dimensions_returns_minus_one(self):
        """
        Тест 4 (Отрицательные параметры):
        Проверка возврата -1 при передаче отрицательных размеров (param_1 или param_2)
        или нулевых физических габаритов.
        """
        # Отрицательный param_1
        self.assertEqual(
            calculate_material_requirement(1, 1, 10, -5.0, 2.0, self.db),
            -1
        )
        # Отрицательный param_2
        self.assertEqual(
            calculate_material_requirement(1, 1, 10, 5.0, -2.0, self.db),
            -1
        )
        # Нулевой param_1
        self.assertEqual(
            calculate_material_requirement(1, 1, 10, 0.0, 2.0, self.db),
            -1
        )
        # Нулевой param_2
        self.assertEqual(
            calculate_material_requirement(1, 1, 10, 5.0, 0.0, self.db),
            -1
        )

    def test_05_zero_or_negative_quantity_returns_minus_one(self):
        """
        Тест 5 (Нулевое количество):
        Проверка возврата -1, если количество продукции равно нулю или меньше.
        """
        # Нулевое количество (quantity = 0)
        self.assertEqual(
            calculate_material_requirement(1, 1, 0, 1.5, 2.0, self.db),
            -1
        )
        # Отрицательное количество (quantity = -10)
        self.assertEqual(
            calculate_material_requirement(1, 1, -10, 1.5, 2.0, self.db),
            -1
        )

    def test_06_invalid_data_types_returns_minus_one(self):
        """
        Дополнительный тест:
        Проверка отказоустойчивости при передаче строк, None или нечисловых типов.
        """
        self.assertEqual(
            calculate_material_requirement("1", 1, 10, 1.0, 1.0, self.db), # type: ignore
            -1
        )
        self.assertEqual(
            calculate_material_requirement(1, None, 10, 1.0, 1.0, self.db), # type: ignore
            -1
        )
        self.assertEqual(
            calculate_material_requirement(1, 1, "10", 1.0, 1.0, self.db), # type: ignore
            -1
        )


if __name__ == "__main__":
    unittest.main()
