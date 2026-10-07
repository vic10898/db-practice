# -*- coding: utf-8 -*-
import unittest
from db_manager import DatabaseManager, DatabaseConnectionError, DatabaseIntegrityError


class TestSecurityAudit(unittest.TestCase):
    """
    Модульные тесты аудита безопасности и устойчивости к SQL-инъекциям.
    Проверяют обязательную параметризацию запросов в СУБД.
    """

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_search_injection_tautology(self):
        """Проверка текстового поиска на инъекцию тавтологии: ' OR '1'='1."""
        injection_payload = "' OR '1'='1"
        results = self.db.get_all_partners(search_query=injection_payload)
        # Параметризованный запрос ищет буквально подстроку "' OR '1'='1", а не выполняет условие
        self.assertEqual(len(results), 0)

    def test_search_injection_destructive_drop(self):
        """Проверка текстового поиска на деструктивную инъекцию: '; DROP TABLE partners; --."""
        destructive_payload = "'; DROP TABLE partners; --"
        results = self.db.get_all_partners(search_query=destructive_payload)
        self.assertEqual(len(results), 0)

        # Проверяем, что таблица partners не была удалена
        partners = self.db.get_all_partners()
        self.assertGreaterEqual(len(partners), 5)

    def test_add_partner_special_characters_escaping(self):
        """Проверка безопасного сохранения полей со спецсимволами и кавычками."""
        malicious_data = {
            "partner_name": "ООО 'Хакер' -- ; DROP TABLE partners;",
            "partner_type": "ООО",
            "rating": 10,
            "inn": "7712345678",
            "email": "hacker_test@sec.org",
            "phone": "+7 999 666-66-66",
            "director": "Иванов \"Хакер\" ' OR 1=1",
            "address": "г. Москва, ул. Безопасности, 1"
        }
        new_id = self.db.add_partner(malicious_data)
        self.assertIsNotNone(new_id)

        # Извлечение сохраненной записи и проверка точного соответствия тексту
        saved = self.db.get_partner_by_id(new_id)
        self.assertEqual(saved["partner_name"], "ООО 'Хакер' -- ; DROP TABLE partners;")
        self.assertEqual(saved["director"], "Иванов \"Хакер\" ' OR 1=1")

    def test_update_partner_sql_injection(self):
        """Проверка параметризации UPDATE при попытке инъекции в полях."""
        update_data = {
            "partner_name": "Вектор'; UPDATE partners SET rating = 9999; --",
            "partner_type": "ООО",
            "rating": 15,
            "inn": "7701234567",
            "email": "vector@mail.ru",
            "phone": "+7 999 000-00-00",
            "director": "Руководитель",
            "address": "г. Москва"
        }
        self.db.update_partner(1, update_data)

        # Рейтинги остальных партнеров не должны были измениться на 9999
        partner_2 = self.db.get_partner_by_id(2)
        self.assertEqual(partner_2["rating"], 10)

    def test_sales_history_query_parameterization(self):
        """Проверка параметризации выборки истории реализации."""
        # Передача несуществующего отрицательного ID не должна вызывать SQL-ошибку
        sales = self.db.get_partner_sales_history(-999)
        self.assertEqual(len(sales), 0)


if __name__ == "__main__":
    unittest.main()
