# -*- coding: utf-8 -*-
import unittest
from discount_calculator import calculate_partner_discount


class TestDiscountCalculator(unittest.TestCase):
    """Набор тестов для алгоритма расчета накопительной скидки партнера."""

    def test_zero_sales(self):
        """Проверка нулевого объема продаж: скидка 0%."""
        self.assertEqual(calculate_partner_discount(0), 0)

    def test_below_10000(self):
        """Проверка объема менее 10 000: скидка 0%."""
        self.assertEqual(calculate_partner_discount(9999), 0)
        self.assertEqual(calculate_partner_discount(500), 0)

    def test_boundary_10000(self):
        """Граничное значение 10 000: скидка 5%."""
        self.assertEqual(calculate_partner_discount(10000), 5)

    def test_between_10000_and_49999(self):
        """Диапазон 10 000 – 49 999: скидка 5%."""
        self.assertEqual(calculate_partner_discount(25000), 5)
        self.assertEqual(calculate_partner_discount(49999), 5)

    def test_boundary_50000(self):
        """Граничное значение 50 000: скидка 10%."""
        self.assertEqual(calculate_partner_discount(50000), 10)

    def test_between_50000_and_299999(self):
        """Диапазон 50 000 – 299 999: скидка 10%."""
        self.assertEqual(calculate_partner_discount(150000), 10)
        self.assertEqual(calculate_partner_discount(299999), 10)

    def test_boundary_300000_and_above(self):
        """Граничное значение 300 000 и выше: скидка 15%."""
        self.assertEqual(calculate_partner_discount(300000), 15)
        self.assertEqual(calculate_partner_discount(500000), 15)

    def test_negative_sales(self):
        """Отрицательный объем: возврат 0%."""
        self.assertEqual(calculate_partner_discount(-100), 0)


if __name__ == "__main__":
    unittest.main()
