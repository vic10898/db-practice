import unittest
from db_manager import DatabaseManager
from material_calculator import calculate_material_requirement


class TestMaterialCalculatorCore(unittest.TestCase):
    """
    Модульные тесты алгоритма расчета сырья и обработки граничных условий.
    """

    def setUp(self):
        self.db = DatabaseManager(db_path=":memory:")

    def test_standard_valid_calculation(self):
        """Проверка стандартного сценария расчета с известным значением."""
        # product_type_id = 1 (коэффициент 4.34)
        # material_type_id = 1 (брак 0.28%)
        # param_1 = 1.5, param_2 = 2.0, quantity = 100
        # 1.5 * 2.0 * 4.34 = 13.02; 13.02 * 100 = 1302; 1302 * 1.0028 = 1305.6456 -> ceil -> 1306
        result = calculate_material_requirement(
            product_type_id=1,
            material_type_id=1,
            quantity=100,
            param_1=1.5,
            param_2=2.0,
            db_manager=self.db
        )
        self.assertEqual(result, 1306)

    def test_ceil_rounding_up(self):
        """Проверка строгого математического округления в большую сторону (ceil)."""
        # param_1 = 1.0, param_2 = 1.0, quantity = 1, product_type = 2 (коэффициент 2.35), material_type = 3 (0.12%)
        # 2.35 * 1.0012 = 2.35282 -> ceil -> 3
        result = calculate_material_requirement(
            product_type_id=2,
            material_type_id=3,
            quantity=1,
            param_1=1.0,
            param_2=1.0,
            db_manager=self.db
        )
        self.assertEqual(result, 3)

    def test_non_existent_product_type_returns_minus_one(self):
        """Проверка возврата -1 при передаче несуществующего ID типа продукции."""
        result = calculate_material_requirement(
            product_type_id=9999,
            material_type_id=1,
            quantity=10,
            param_1=1.0,
            param_2=1.0,
            db_manager=self.db
        )
        self.assertEqual(result, -1)

    def test_non_existent_material_type_returns_minus_one(self):
        """Проверка возврата -1 при передаче несуществующего ID типа материала."""
        result = calculate_material_requirement(
            product_type_id=1,
            material_type_id=8888,
            quantity=10,
            param_1=1.0,
            param_2=1.0,
            db_manager=self.db
        )
        self.assertEqual(result, -1)

    def test_negative_or_zero_dimensions_returns_minus_one(self):
        """Проверка возврата -1 при отрицательных или нулевых параметрах изделия."""
        # Отрицательный param_1
        self.assertEqual(
            calculate_material_requirement(1, 1, 10, -2.5, 3.0, self.db),
            -1
        )
        # Нулевой param_2
        self.assertEqual(
            calculate_material_requirement(1, 1, 10, 2.5, 0.0, self.db),
            -1
        )

    def test_zero_or_negative_quantity_returns_minus_one(self):
        """Проверка возврата -1 при количестве продукции <= 0."""
        self.assertEqual(
            calculate_material_requirement(1, 1, 0, 1.0, 1.0, self.db),
            -1
        )
        self.assertEqual(
            calculate_material_requirement(1, 1, -50, 1.0, 1.0, self.db),
            -1
        )


if __name__ == "__main__":
    unittest.main()
