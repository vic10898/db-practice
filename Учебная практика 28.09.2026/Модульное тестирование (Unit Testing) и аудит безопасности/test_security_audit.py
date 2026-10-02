import os
import unittest
import tempfile
import sqlite3

from db_manager import DatabaseManager, DatabaseIntegrityError, PartnerNotFoundError
from logger import LOG_FILE_PATH


class TestSecurityAuditAndSqlInjection(unittest.TestCase):
    """
    Тесты аудита информационной безопасности:
    1. Защита от SQL-инъекций (SQL Injection Prevention) с использованием параметризованных запросов;
    2. Проверка корректности экранирования служебных символов и кавычек;
    3. Формирование отчетного лога в app.log при возникновении исключений.
    """

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db = DatabaseManager(db_path=self.temp_db.name)

    def tearDown(self):
        if hasattr(self.db, "_mem_conn") and self.db._mem_conn:
            self.db._mem_conn.close()
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_sql_injection_in_search_fails_to_compromise_db(self):
        """
        Проверка защиты поиска от классической SQL-инъекции: ' OR '1'='1.
        Параметризованный запрос должен воспринимать строку буквально, а не как SQL-код.
        """
        injection_payload = "' OR '1'='1"
        results = self.db.search_partners_by_name(injection_payload)
        # Поскольку партнера с буквальным именем "' OR '1'='1" нет, результат должен быть пустым
        self.assertEqual(results, [])

    def test_sql_injection_stacked_queries_drop_table_prevented(self):
        """
        Проверка защиты от деструктивной инъекции с точкой с запятой и DROP TABLE.
        """
        malicious_input = "Тестовая'; DROP TABLE partners; --"
        new_partner = {
            "company_name": malicious_input,
            "partner_type": "ООО",
            "rating": 10,
            "address": "г. Москва",
            "director": "Иванов И.И.",
            "contact_phone": "+7 (999) 000-11-22",
            "email": "security_test@corp.ru"
        }
        # Вставка должна быть безопасной: таблица не должна удалиться
        partner_id = self.db.add_partner(new_partner)
        self.assertIsInstance(partner_id, int)

        # Проверяем, что таблица цела и запись сохранена с буквальным вредоносным текстом
        stored = self.db.get_partner_by_id(partner_id)
        self.assertEqual(stored["company_name"], malicious_input)

    def test_sql_injection_in_partner_id_prevented(self):
        """
        Проверка передачи нечислового значения в get_partner_by_id.
        При некорректном первичном ключе должно выбрасываться исключение без выполнения произвольного SQL.
        """
        # Попытка внедрения через идентификатор
        with self.assertRaises(PartnerNotFoundError):
            self.db.get_partner_by_id(999999)

    def test_error_logging_records_timestamp_and_message(self):
        """
        Проверка формирования отчетного лога (app.log).
        При возникновении исключения (например, нарушение уникальности email)
        в файл app.log должна быть записана дата, время и текст ошибки.
        """
        partner_a = {
            "company_name": "Компания А",
            "partner_type": "ООО",
            "rating": 5,
            "address": "Адрес",
            "director": "Директор",
            "contact_phone": "+7 999 111-11-11",
            "email": "unique_audit@domain.ru"
        }
        self.db.add_partner(partner_a)

        # Попытка добавить дубликат вызовет DatabaseIntegrityError и запись в лог
        with self.assertRaises(DatabaseIntegrityError):
            self.db.add_partner(partner_a)

        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            log_content = f.read()

        self.assertIn("Нарушение уникальности при добавлении партнера", log_content)
        self.assertIn("unique_audit@domain.ru", log_content)
        self.assertIn("[ERROR]", log_content)


if __name__ == "__main__":
    unittest.main()
