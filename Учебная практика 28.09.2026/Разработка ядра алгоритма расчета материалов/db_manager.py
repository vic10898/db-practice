import os
import sys
import sqlite3

current_dir = os.path.dirname(os.path.abspath(__file__))


class DatabaseManager:
    """
    Менеджер базы данных для модуля расчета материалов.
    Предоставляет доступ к справочникам типов продукции и материалов.
    """

    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = os.path.join(current_dir, "materials.db")
        else:
            self.db_path = db_path
        self._mem_conn = None
        self._init_database()

    def get_connection(self):
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

    def _close_conn(self, conn):
        if self.db_path != ":memory:":
            conn.close()

    def _init_database(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Справочник типов продукции
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT NOT NULL UNIQUE,
                    coefficient REAL NOT NULL
                );
            """)

            # Справочник типов материалов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS material_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT NOT NULL UNIQUE,
                    defect_rate REAL NOT NULL
                );
            """)

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

            conn.commit()
        finally:
            self._close_conn(conn)

    def get_product_type_coefficient(self, product_type_id: int):
        """Возвращает коэффициент типа продукции или None, если тип не найден."""
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

    def get_material_defect_rate(self, material_type_id: int):
        """Возвращает процент брака материала или None, если тип не найден."""
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

    def get_all_product_types(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, type_name, coefficient FROM product_types ORDER BY id ASC;")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            self._close_conn(conn)

    def get_all_material_types(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, type_name, defect_rate FROM material_types ORDER BY id ASC;")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            self._close_conn(conn)
