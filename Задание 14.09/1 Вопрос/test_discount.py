import unittest
from discount import calculate_partner_discount


class TestPartnerDiscount(unittest.TestCase):
    """Набор тестов для функции расчета партнерской скидки."""

    def test_boundary_values(self):
        """Проверка пограничных значений из ТЗ."""
        # Менее 10 000 ед. -> 0%
        self.assertEqual(calculate_partner_discount(9999), 0)

        # От 10 000 до 49 999 ед. -> 5%
        self.assertEqual(calculate_partner_discount(10000), 5)
        self.assertEqual(calculate_partner_discount(49999), 5)

        # От 50 000 до 299 999 ед. -> 10%
        self.assertEqual(calculate_partner_discount(50000), 10)
        self.assertEqual(calculate_partner_discount(299999), 10)

        # От 300 000 ед. и более -> 15%
        self.assertEqual(calculate_partner_discount(300000), 15)

    def test_zero_and_intermediate_values(self):
        """Проверка нулевого и промежуточных значений внутри диапазонов."""
        self.assertEqual(calculate_partner_discount(0), 0)
        self.assertEqual(calculate_partner_discount(5000), 0)
        self.assertEqual(calculate_partner_discount(25000), 5)
        self.assertEqual(calculate_partner_discount(150000), 10)
        self.assertEqual(calculate_partner_discount(600000), 15)

    def test_negative_values_raise_value_error(self):
        """Проверка генерации ValueError при отрицательном объеме продаж."""
        with self.assertRaises(ValueError):
            calculate_partner_discount(-1)

        with self.assertRaises(ValueError):
            calculate_partner_discount(-500)

    def test_invalid_types_raise_type_error(self):
        """Проверка генерации TypeError при передаче аргумента некорректного типа."""
        with self.assertRaises(TypeError):
            calculate_partner_discount("10000")

        with self.assertRaises(TypeError):
            calculate_partner_discount(15000.5)

        with self.assertRaises(TypeError):
            calculate_partner_discount(None)

        with self.assertRaises(TypeError):
            calculate_partner_discount(True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
