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
    Модуль взаимодействия с БД: управление партнерами,
    продукцией, типами материалов и историей поставок.
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

            # 1. Справочник партнеров
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

            # 2. Справочник типов продукции
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT NOT NULL UNIQUE,
                    coefficient REAL NOT NULL
                );
            """)

            # 3. Справочник типов материалов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS material_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT NOT NULL UNIQUE,
                    defect_rate REAL NOT NULL
                );
            """)

            # 4. Справочник продукции
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    product_type_id INTEGER NOT NULL,
                    base_price REAL NOT NULL,
                    FOREIGN KEY (product_type_id) REFERENCES product_types (id)
                );
            """)

            # 5. История поставок и реализации
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

            # Первичное заполнение справочников типов продукции
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

            # Первичное заполнение справочников материалов
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

            # Первичное заполнение каталога продукции
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

            # Первичное заполнение партнеров
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

            # Первичное заполнение истории отгрузок
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
        finally:
            self._close_conn(conn)

    def get_partner_by_id(self, partner_id: int) -> dict:
        query = "SELECT * FROM partners WHERE id = ?;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (partner_id,))
            row = cursor.fetchone()
            if not row:
                raise PartnerNotFoundError(f"Партнер с идентификатором #{partner_id} не найден в базе данных.")
            return dict(row)
        finally:
            self._close_conn(conn)

    def get_partner_sales_history(self, partner_id: int) -> list:
        """
        Получение детальной истории отгрузок конкретного партнера.
        Используется JOIN между таблицами deliveries и products.
        """
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
        finally:
            self._close_conn(conn)

    def get_product_types(self) -> list:
        """Справочник типов продукции с коэффициентами."""
        query = "SELECT id, type_name, coefficient FROM product_types ORDER BY id ASC;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            self._close_conn(conn)

    def get_product_type_coefficient(self, product_type_id: int):
        """Возвращает нормативный коэффициент типа продукции либо None."""
        if not isinstance(product_type_id, int):
            return None
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT coefficient FROM product_types WHERE id = ?;", (product_type_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return float(row["coefficient"])
        finally:
            self._close_conn(conn)

    def get_material_types(self) -> list:
        """Справочник типов материалов с процентом брака."""
        query = "SELECT id, type_name, defect_rate FROM material_types ORDER BY id ASC;"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            self._close_conn(conn)

    def get_material_defect_rate(self, material_type_id: int):
        """Возвращает процент брака материала либо None."""
        if not isinstance(material_type_id, int):
            return None
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT defect_rate FROM material_types WHERE id = ?;", (material_type_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return float(row["defect_rate"])
        finally:
            self._close_conn(conn)

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
            raise DatabaseIntegrityError(
                f"Партнер с адресом электронной почты «{data.get('email')}» уже существует в системе.\n\n"
                f"Пожалуйста, укажите уникальный Email организации."
            )
        finally:
            self._close_conn(conn)

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
            raise DatabaseIntegrityError(
                f"Невозможно обновить запись: Email «{data.get('email')}» уже используется другой компанией.\n\n"
                f"Пожалуйста, измените адрес электронной почты."
            )
        finally:
            self._close_conn(conn)
