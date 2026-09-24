import os
import sys
import sqlite3

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
core_dir = os.path.join(parent_dir, "Задание 14.09", "Разработка ядра")
if os.path.exists(core_dir):
    sys.path.append(core_dir)

try:
    from discount import calculate_partner_discount
except ImportError:
    def calculate_partner_discount(sales_volume: int) -> int:
        if sales_volume < 10000:
            return 0
        elif sales_volume < 50000:
            return 5
        elif sales_volume < 300000:
            return 10
        return 15


class IntegrityViolationError(Exception):
    """Исключение при нарушении ссылочной целостности базы данных."""
    pass


class PartnerNotFoundError(Exception):
    """Исключение при попытке обновить несуществующего партнера."""
    pass


class DatabaseManager:
    """
    Класс управления доступом к базе данных и выполнения CRUD-операций.
    Поддерживает транзакционность, контроль целостности данных и работу с SQLite.
    """

    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = os.path.join(current_dir, "partners.db")
        else:
            self.db_path = db_path
        self._init_database()

    def get_connection(self):
        """Возвращает соединение со словарем в качестве фабрики строк."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_database(self):
        """Инициализация схемы таблиц и тестовых данных при первом запуске."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS partners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    partner_type TEXT NOT NULL DEFAULT 'ООО',
                    rating INTEGER NOT NULL DEFAULT 0,
                    address TEXT,
                    director TEXT,
                    contact_phone TEXT,
                    email TEXT NOT NULL UNIQUE
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    delivery_date TEXT NOT NULL,
                    FOREIGN KEY (partner_id) REFERENCES partners (id) ON DELETE CASCADE
                );
            """)

            cursor.execute("SELECT COUNT(*) FROM partners;")
            if cursor.fetchone()[0] == 0:
                seed_partners = [
                    (1, "Логистик-Экспресс", "ООО", 10, "г. Москва, ул. Ленина, д. 15", "Иванов И.И.", "+7 (999) 111-22-33", "info@logex.ru"),
                    (2, "Петров А.В.", "ИП", 8, "г. Санкт-Петербург, Невский пр., д. 40", "Петров А.В.", "+7 (999) 222-33-44", "petrov@mail.ru"),
                    (3, "Быстрый Путь", "ЗАО", 12, "г. Казань, ул. Баумана, д. 20", "Сидоров С.С.", "+7 (812) 555-44-33", "speedway@yandex.ru"),
                    (4, "ТехноСнаб", "ООО", 5, "г. Новосибирск, Красный пр., д. 10", "Михайлов М.М.", "+7 (383) 999-88-77", "technosnab@mail.ru")
                ]
                cursor.executemany("""
                    INSERT INTO partners (id, company_name, partner_type, rating, address, director, contact_phone, email)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, seed_partners)

                seed_deliveries = [
                    (101, 1, 1, 80, "2026-03-01"),
                    (102, 2, 2, 15000, "2026-03-15"),
                    (103, 3, 1, 65000, "2026-03-20")
                ]
                cursor.executemany("""
                    INSERT INTO deliveries (id, partner_id, product_id, quantity, delivery_date)
                    VALUES (?, ?, ?, ?, ?);
                """, seed_deliveries)

            conn.commit()
        finally:
            conn.close()

    def get_all_partners(self) -> list:
        query = """
            SELECT 
                p.id,
                p.company_name,
                p.partner_type,
                p.rating,
                p.address,
                p.director,
                p.contact_phone,
                p.email,
                COALESCE(SUM(d.quantity), 0) AS total_sales
            FROM partners p
            LEFT JOIN deliveries d ON p.id = d.partner_id
            GROUP BY p.id, p.company_name, p.partner_type, p.rating, p.address, p.director, p.contact_phone, p.email
            ORDER BY p.id ASC;
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            result = []
            for r in rows:
                total_sales = int(r["total_sales"])
                discount = calculate_partner_discount(total_sales)
                result.append({
                    "id": r["id"],
                    "company_name": r["company_name"],
                    "partner_type": r["partner_type"],
                    "rating": r["rating"],
                    "address": r["address"] or "",
                    "director": r["director"] or "",
                    "contact_phone": r["contact_phone"] or "",
                    "email": r["email"] or "",
                    "total_sales": total_sales,
                    "discount": discount
                })
            return result
        finally:
            conn.close()

    def get_partner_by_id(self, partner_id: int) -> dict:
        query = "SELECT * FROM partners WHERE id = ?;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (partner_id,))
            row = cursor.fetchone()
            if not row:
                raise PartnerNotFoundError(f"Партнер с ID {partner_id} не найден в базе данных.")
            return dict(row)
        finally:
            conn.close()

    def add_partner(self, data: dict) -> int:
        query = """
            INSERT INTO partners (company_name, partner_type, rating, address, director, contact_phone, email)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (
                data["company_name"],
                data.get("partner_type", "ООО"),
                int(data.get("rating", 0)),
                data.get("address", ""),
                data.get("director", ""),
                data.get("contact_phone", ""),
                data["email"]
            ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.rollback()
            raise IntegrityViolationError(f"Ошибка целостности: Email '{data.get('email')}' уже зарегистрирован в базе.")
        finally:
            conn.close()

    def update_partner(self, partner_id: int, data: dict):
        self.get_partner_by_id(partner_id)

        query = """
            UPDATE partners
            SET company_name = ?,
                partner_type = ?,
                rating = ?,
                address = ?,
                director = ?,
                contact_phone = ?,
                email = ?
            WHERE id = ?;
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (
                data["company_name"],
                data.get("partner_type", "ООО"),
                int(data.get("rating", 0)),
                data.get("address", ""),
                data.get("director", ""),
                data.get("contact_phone", ""),
                data["email"],
                partner_id
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            raise IntegrityViolationError(f"Невозможно обновить: Email '{data.get('email')}' занят другой организацией.")
        finally:
            conn.close()
