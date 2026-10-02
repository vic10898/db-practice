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

from logger import log_exception, app_logger


class DatabaseConnectionError(Exception):
    """Исключение при недоступности СУБД или сбое подключения."""
    pass


class DatabaseIntegrityError(Exception):
    """Исключение при нарушении ограничений базы данных."""
    pass


class PartnerNotFoundError(Exception):
    """Исключение при запросе несуществующей записи."""
    pass


class DatabaseManager:
    """
    Модуль взаимодействия с БД с аудитом безопасности:
    — 100% защита от SQL-инъекций через параметризованные запросы;
    — Автоматическое протоколирование всех исключений в файл app.log.
    """

    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = os.path.join(current_dir, "partners.db")
        else:
            self.db_path = db_path
        self._mem_conn = None
        self._init_database()

    def get_connection(self):
        try:
            if self.db_path == ":memory:":
                if self._mem_conn is None:
                    self._mem_conn = sqlite3.connect(":memory:")
                    self._mem_conn.row_factory = sqlite3.Row
                    self._mem_conn.execute("PRAGMA foreign_keys = ON;")
                return self._mem_conn

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except sqlite3.Error as err:
            log_exception("Сбой при попытке подключения к базе данных", err)
            raise DatabaseConnectionError(
                f"СУБД недоступна или поврежден файл базы данных.\n"
                f"Пожалуйста, проверьте права доступа к файлу '{self.db_path}'.\nДетали: {err}"
            )

    def _close_conn(self, conn):
        if self.db_path != ":memory:":
            conn.close()

    def _init_database(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Таблица партнеров
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

            # Таблица типов продукции
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT NOT NULL UNIQUE,
                    coefficient REAL NOT NULL
                );
            """)

            # Таблица типов материалов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS material_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT NOT NULL UNIQUE,
                    defect_rate REAL NOT NULL
                );
            """)

            # Таблица продукции
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    product_type_id INTEGER NOT NULL,
                    base_price REAL NOT NULL,
                    FOREIGN KEY (product_type_id) REFERENCES product_types (id)
                );
            """)

            # Таблица поставок
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    delivery_date TEXT NOT NULL,
                    FOREIGN KEY (partner_id) REFERENCES partners (id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
                );
            """)

            # Заполнение нормативных справочников
            cursor.execute("SELECT COUNT(*) FROM product_types;")
            if cursor.fetchone()[0] == 0:
                seed_product_types = [
                    (1, "Паркетная доска", 4.34),
                    (2, "Ламинат", 2.35),
                    (3, "Массивная доска", 5.15),
                    (4, "Пробковое покрытие", 1.50)
                ]
                cursor.executemany("""
                    INSERT INTO product_types (id, type_name, coefficient)
                    VALUES (?, ?, ?);
                """, seed_product_types)

            cursor.execute("SELECT COUNT(*) FROM material_types;")
            if cursor.fetchone()[0] == 0:
                seed_materials = [
                    (1, "Тип материала 1 (Дубовый шпон)", 0.28),
                    (2, "Тип материала 2 (Хвойная подложка)", 0.55),
                    (3, "Тип материала 3 (Защитный лак)", 0.12),
                    (4, "Тип материала 4 (Пробковая гранула)", 0.85)
                ]
                cursor.executemany("""
                    INSERT INTO material_types (id, type_name, defect_rate)
                    VALUES (?, ?, ?);
                """, seed_materials)

            cursor.execute("SELECT COUNT(*) FROM products;")
            if cursor.fetchone()[0] == 0:
                seed_products = [
                    (1, "Паркет Дуб Натуральный 14 мм", 1, 3200.0),
                    (2, "Ламинат Сосна Скандинавская 8 мм", 2, 850.0),
                    (3, "Массивная доска Ясень Классик 18 мм", 3, 4500.0),
                    (4, "Пробка Порто Натурал 6 мм", 4, 1900.0),
                    (5, "Ламинат Дуб Мореный 10 мм", 2, 1150.0)
                ]
                cursor.executemany("""
                    INSERT INTO products (id, product_name, product_type_id, base_price)
                    VALUES (?, ?, ?, ?);
                """, seed_products)

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

            cursor.execute("SELECT COUNT(*) FROM deliveries;")
            if cursor.fetchone()[0] == 0:
                seed_deliveries = [
                    (101, 1, 1, 80, "2026-03-01"),
                    (102, 1, 2, 450, "2026-03-12"),
                    (103, 1, 5, 200, "2026-03-28"),
                    (104, 2, 2, 15000, "2026-03-15"),
                    (105, 2, 3, 3000, "2026-03-22"),
                    (106, 3, 1, 65000, "2026-03-20"),
                    (107, 3, 4, 12000, "2026-04-05"),
                    (108, 4, 2, 550, "2026-04-10")
                ]
                cursor.executemany("""
                    INSERT INTO deliveries (id, partner_id, product_id, quantity, delivery_date)
                    VALUES (?, ?, ?, ?, ?);
                """, seed_deliveries)

            conn.commit()
        except sqlite3.Error as err:
            log_exception("Сбой инициализации схемы базы данных", err)
            raise
        finally:
            self._close_conn(conn)

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
                sales = int(r["total_sales"])
                result.append({
                    "id": r["id"],
                    "company_name": r["company_name"],
                    "partner_type": r["partner_type"],
                    "rating": r["rating"],
                    "address": r["address"] or "",
                    "director": r["director"] or "",
                    "contact_phone": r["contact_phone"] or "",
                    "email": r["email"] or "",
                    "total_sales": sales,
                    "discount": calculate_partner_discount(sales)
                })
            return result
        except sqlite3.Error as err:
            log_exception("Ошибка при чтении списка контрагентов", err)
            raise DatabaseConnectionError(str(err))
        finally:
            self._close_conn(conn)

    def get_partner_by_id(self, partner_id: int) -> dict:
        """Параметризованный запрос получения партнера по первичному ключу."""
        query = "SELECT * FROM partners WHERE id = ?;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (partner_id,))
            row = cursor.fetchone()
            if not row:
                err_msg = f"Партнер с идентификатором #{partner_id} не найден в базе данных."
                log_exception(err_msg)
                raise PartnerNotFoundError(err_msg)
            return dict(row)
        except sqlite3.Error as err:
            log_exception(f"Ошибка выполнения SQL при поиске партнера #{partner_id}", err)
            raise DatabaseConnectionError(str(err))
        finally:
            self._close_conn(conn)

    def get_partner_sales_history(self, partner_id: int) -> list:
        """Параметризованный SQL JOIN для получения истории отгрузок."""
        query = """
            SELECT 
                p.product_name,
                d.quantity,
                d.delivery_date
            FROM deliveries d
            JOIN products p ON d.product_id = p.id
            WHERE d.partner_id = ?
            ORDER BY d.delivery_date DESC;
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (partner_id,))
            rows = cursor.fetchall()
            return [
                {
                    "product_name": r["product_name"],
                    "quantity": int(r["quantity"]),
                    "delivery_date": r["delivery_date"]
                }
                for r in rows
            ]
        except sqlite3.Error as err:
            log_exception(f"Ошибка при получении истории продаж для партнера #{partner_id}", err)
            raise DatabaseConnectionError(str(err))
        finally:
            self._close_conn(conn)

    def get_product_types(self) -> list:
        query = "SELECT id, type_name, coefficient FROM product_types ORDER BY id ASC;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(r) for r in cursor.fetchall()]
        except sqlite3.Error as err:
            log_exception("Ошибка при чтении типов продукции", err)
            raise DatabaseConnectionError(str(err))
        finally:
            self._close_conn(conn)

    def get_product_type_coefficient(self, product_type_id: int):
        if not isinstance(product_type_id, int):
            return None
        query = "SELECT coefficient FROM product_types WHERE id = ?;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (product_type_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return float(row["coefficient"])
        except sqlite3.Error as err:
            log_exception(f"Ошибка при чтении коэффициента типа продукции #{product_type_id}", err)
            return None
        finally:
            self._close_conn(conn)

    def get_material_types(self) -> list:
        query = "SELECT id, type_name, defect_rate FROM material_types ORDER BY id ASC;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(r) for r in cursor.fetchall()]
        except sqlite3.Error as err:
            log_exception("Ошибка при чтении типов материалов", err)
            raise DatabaseConnectionError(str(err))
        finally:
            self._close_conn(conn)

    def get_material_defect_rate(self, material_type_id: int):
        if not isinstance(material_type_id, int):
            return None
        query = "SELECT defect_rate FROM material_types WHERE id = ?;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (material_type_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return float(row["defect_rate"])
        except sqlite3.Error as err:
            log_exception(f"Ошибка при чтении процента брака материала #{material_type_id}", err)
            return None
        finally:
            self._close_conn(conn)

    def search_partners_by_name(self, search_term: str) -> list:
        """
        Безопасный параметризованный поиск партнеров по наименованию (защита от SQLi).
        """
        query = "SELECT id, company_name, email FROM partners WHERE company_name LIKE ? ORDER BY id ASC;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            pattern = f"%{search_term}%"
            cursor.execute(query, (pattern,))
            return [dict(r) for r in cursor.fetchall()]
        except sqlite3.Error as err:
            log_exception(f"Ошибка параметризованного поиска по термину '{search_term}'", err)
            raise DatabaseConnectionError(str(err))
        finally:
            self._close_conn(conn)

    def add_partner(self, data: dict) -> int:
        """Параметризованная вставка данных (INSERT)."""
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
        except sqlite3.IntegrityError as err:
            conn.rollback()
            log_exception(f"Нарушение уникальности при добавлении партнера с Email '{data.get('email')}'", err)
            raise DatabaseIntegrityError(
                f"Партнер с адресом электронной почты «{data.get('email')}» уже существует в системе.\n\n"
                f"Пожалуйста, укажите уникальный Email организации."
            )
        except sqlite3.Error as err:
            conn.rollback()
            log_exception("Сбой СУБД при добавлении контрагента", err)
            raise DatabaseConnectionError(str(err))
        finally:
            self._close_conn(conn)

    def update_partner(self, partner_id: int, data: dict):
        """Параметризованное обновление данных (UPDATE)."""
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
        except sqlite3.IntegrityError as err:
            conn.rollback()
            log_exception(f"Нарушение уникальности Email при обновлении контрагента #{partner_id}", err)
            raise DatabaseIntegrityError(
                f"Невозможно обновить запись: Email «{data.get('email')}» уже используется другой компанией.\n\n"
                f"Пожалуйста, измените адрес электронной почты."
            )
        except sqlite3.Error as err:
            conn.rollback()
            log_exception(f"Сбой СУБД при обновлении контрагента #{partner_id}", err)
            raise DatabaseConnectionError(str(err))
        finally:
            self._close_conn(conn)
