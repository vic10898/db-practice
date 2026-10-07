# -*- coding: utf-8 -*-
import os
import sys
import math
import sqlite3
from typing import List, Dict, Any, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
etl_db_path = os.path.join(
    parent_dir,
    "Инфраструктура данных и ETL (База данных в 3NF)",
    "database.db"
)


def calculate_partner_discount(sales_volume: int) -> int:
    """Расчет скидки партнера по шкале объемов продаж."""
    if sales_volume < 10000:
        return 0
    elif sales_volume < 50000:
        return 5
    elif sales_volume < 300000:
        return 10
    return 15


class DatabaseConnectionError(Exception):
    """Исключение при недоступности базы данных."""
    pass


class DatabaseIntegrityError(Exception):
    """Исключение при нарушении ограничений целостности."""
    pass


class PartnerNotFoundError(Exception):
    """Исключение при отсутствии записи партнера."""
    pass


class DatabaseManager:
    """Центральный менеджер взаимодействия с базой данных CRM-системы."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(current_dir, "partners.db")
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
                f"Не удалось подключиться к базе данных.\n"
                f"Файл: '{self.db_path}'.\nДетали: {err}"
            )

    def close_connection(self, conn):
        if self.db_path != ":memory:":
            conn.close()

    def _init_database(self):
        """Создание таблиц и начальное заполнение данными."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_types (
                product_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name VARCHAR(255) NOT NULL UNIQUE,
                coefficient REAL NOT NULL CHECK (coefficient > 0)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS material_types (
                material_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name VARCHAR(255) NOT NULL UNIQUE,
                defect_rate REAL NOT NULL CHECK (defect_rate >= 0)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS partners (
                partner_id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_name VARCHAR(255) NOT NULL,
                partner_type VARCHAR(50) NOT NULL DEFAULT 'ООО',
                rating INTEGER NOT NULL DEFAULT 0 CHECK (rating >= 0),
                address VARCHAR(255),
                director VARCHAR(255),
                phone VARCHAR(50),
                inn VARCHAR(12) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name VARCHAR(255) NOT NULL,
                product_type_id INTEGER,
                price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
                FOREIGN KEY (product_type_id) REFERENCES product_types (product_type_id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_history (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                sale_date DATE NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                amount DECIMAL(12, 2) NOT NULL CHECK (amount >= 0),
                FOREIGN KEY (partner_id) REFERENCES partners (partner_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE RESTRICT
            );
        """)

        # Заполнение справочников при пустой таблице
        cursor.execute("SELECT COUNT(*) FROM product_types;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO product_types (product_type_id, type_name, coefficient)
                VALUES (?, ?, ?);
            """, [
                (1, "Паркетная доска", 4.34),
                (2, "Ламинат", 2.35),
                (3, "Массивная доска", 5.15),
                (4, "Пробковое покрытие", 1.50)
            ])

        cursor.execute("SELECT COUNT(*) FROM material_types;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO material_types (material_type_id, type_name, defect_rate)
                VALUES (?, ?, ?);
            """, [
                (1, "Тип материала 1 (Дубовый шпон)", 0.28),
                (2, "Тип материала 2 (Хвойная подложка)", 0.55),
                (3, "Тип материала 3 (Защитный лак)", 0.12),
                (4, "Тип материала 4 (Пробковая гранула)", 0.85)
            ])

        # Если партнеры еще не заведены, заполнить данными из задания
        cursor.execute("SELECT COUNT(*) FROM partners;")
        if cursor.fetchone()[0] == 0:
            seed_partners = [
                (1, 'ООО "Вектор"', 'ООО', 10, 'г. Москва, ул. Производственная, 12', 'Руководитель', '+7 999 000-00-00', '7701234567', 'vector@mail.ru'),
                (2, 'ИП ...Петров A.B.', 'ИП', 10, 'г. Москва, ул. Производственная, 12', 'Руководитель', '+7 999 000-00-00', '7802345678', 'petrov@yandex.ru'),
                (3, 'АО "Технолоджис"', 'АО', 10, 'г. Москва, ул. Производственная, 12', 'Руководитель', '+7 999 000-00-00', '5003456789', 'info@techno.ru'),
                (4, 'ООО "Альфа"', 'ООО', 10, 'г. Москва, ул. Производственная, 12', 'Руководитель', '+7 999 000-00-00', '7704567890', 'alpha@gmail.com'),
                (5, 'ИП Сидоров И.И.', 'ИП', 10, 'г. Москва, ул. Производственная, 12', 'Руководитель', '+7 999 000-00-00', '7805678901', 'sidorov@llc.ru')
            ]
            cursor.executemany("""
                INSERT INTO partners (partner_id, partner_name, partner_type, rating, address, director, phone, inn, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, seed_partners)

            seed_products = [
                (101, "Ноутбук Pro", 1, 75000.00),
                (102, "Смартфон X", 2, 45000.50),
                (103, 'Монитор 27"', 3, 18200.00)
            ]
            cursor.executemany("""
                INSERT INTO products (product_id, product_name, product_type_id, price)
                VALUES (?, ?, ?, ?);
            """, seed_products)

            seed_sales = [
                (1001, 1, 101, "2023-10-25", 2, 150000.00),
                (1002, 2, 102, "2023-10-26", 1, 45000.50),
                (1004, 4, 103, "2023-10-28", 10, 182000.00),
                (1005, 3, 102, "2023-10-29", 3, 135001.50),
                (1006, 5, 103, "2023-10-30", 1, 18200.00)
            ]
            cursor.executemany("""
                INSERT INTO sales_history (sale_id, partner_id, product_id, sale_date, quantity, amount)
                VALUES (?, ?, ?, ?, ?, ?);
            """, seed_sales)

        conn.commit()
        self.close_connection(conn)

    def get_all_partners(self, search_query: str = "") -> List[Dict[str, Any]]:
        """
        Получение списка всех партнеров с подсчетом продаж и скидки.
        Безопасный параметризованный запрос с защитой от SQL-инъекций.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    p.partner_id,
                    p.partner_name,
                    p.partner_type,
                    p.rating,
                    p.address,
                    p.director,
                    p.phone,
                    p.inn,
                    p.email,
                    COALESCE(SUM(sh.quantity), 0) AS total_sales
                FROM partners p
                LEFT JOIN sales_history sh ON p.partner_id = sh.partner_id
            """
            params = []
            if search_query:
                clean_search = f"%{search_query.strip()}%"
                query += " WHERE p.partner_name LIKE ? OR p.email LIKE ? OR p.phone LIKE ?"
                params.extend([clean_search, clean_search, clean_search])

            query += " GROUP BY p.partner_id ORDER BY p.partner_id ASC;"
            cursor.execute(query, params)

            rows = cursor.fetchall()
            result = []
            for row in rows:
                p_dict = dict(row)
                p_dict["discount"] = calculate_partner_discount(p_dict["total_sales"])
                result.append(p_dict)
            return result
        finally:
            self.close_connection(conn)

    def get_partner_by_id(self, partner_id: int) -> Dict[str, Any]:
        """Получение данных конкретного контрагента по ID."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.partner_id,
                    p.partner_name,
                    p.partner_type,
                    p.rating,
                    p.address,
                    p.director,
                    p.phone,
                    p.inn,
                    p.email,
                    COALESCE(SUM(sh.quantity), 0) AS total_sales
                FROM partners p
                LEFT JOIN sales_history sh ON p.partner_id = sh.partner_id
                WHERE p.partner_id = ?
                GROUP BY p.partner_id;
            """, (partner_id,))
            row = cursor.fetchone()
            if not row:
                raise PartnerNotFoundError(f"Партнер с ID {partner_id} не найден в базе данных.")
            res = dict(row)
            res["discount"] = calculate_partner_discount(res["total_sales"])
            return res
        finally:
            self.close_connection(conn)

    def add_partner(self, data: Dict[str, Any]) -> int:
        """Добавление нового партнера в базу данных."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO partners (partner_name, partner_type, rating, address, director, phone, inn, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                data["partner_name"],
                data["partner_type"],
                data["rating"],
                data.get("address", ""),
                data.get("director", ""),
                data.get("phone", ""),
                data.get("inn", "0000000000"),
                data["email"]
            ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as err:
            conn.rollback()
            raise DatabaseIntegrityError(f"Ошибка уникальности данных (Email или ИНН уже существуют): {err}")
        finally:
            self.close_connection(conn)

    def update_partner(self, partner_id: int, data: Dict[str, Any]):
        """Обновление реквизитов существующего контрагента."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE partners
                SET partner_name = ?,
                    partner_type = ?,
                    rating = ?,
                    address = ?,
                    director = ?,
                    phone = ?,
                    inn = ?,
                    email = ?
                WHERE partner_id = ?;
            """, (
                data["partner_name"],
                data["partner_type"],
                data["rating"],
                data.get("address", ""),
                data.get("director", ""),
                data.get("phone", ""),
                data.get("inn", "0000000000"),
                data["email"],
                partner_id
            ))
            if cursor.rowcount == 0:
                raise PartnerNotFoundError(f"Партнер с ID {partner_id} не найден для обновления.")
            conn.commit()
        except sqlite3.IntegrityError as err:
            conn.rollback()
            raise DatabaseIntegrityError(f"Ошибка сохранения: Email или ИНН уже используются другим контрагентом ({err}).")
        finally:
            self.close_connection(conn)

    def delete_partner(self, partner_id: int):
        """Удаление партнера с каскадным удалением истории продаж."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM partners WHERE partner_id = ?;", (partner_id,))
            if cursor.rowcount == 0:
                raise PartnerNotFoundError(f"Партнер с ID {partner_id} не найден.")
            conn.commit()
        finally:
            self.close_connection(conn)

    def get_partner_sales_history(self, partner_id: int) -> List[Dict[str, Any]]:
        """Получение истории продаж конкретного партнера."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    sh.sale_id,
                    sh.sale_date,
                    p.product_name,
                    sh.quantity,
                    sh.amount
                FROM sales_history sh
                JOIN products p ON sh.product_id = p.product_id
                WHERE sh.partner_id = ?
                ORDER BY sh.sale_date DESC;
            """, (partner_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            self.close_connection(conn)

    def get_product_types(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT product_type_id, type_name, coefficient FROM product_types ORDER BY product_type_id;")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            self.close_connection(conn)

    def get_material_types(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT material_type_id, type_name, defect_rate FROM material_types ORDER BY material_type_id;")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            self.close_connection(conn)

    def calculate_material(self, count: int, product_type_id: int, material_type_id: int, param1: float, param2: float) -> int:
        if count < 0 or param1 < 0 or param2 < 0:
            return -1
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT coefficient FROM product_types WHERE product_type_id = ?;", (product_type_id,))
            row_prod = cursor.fetchone()
            if not row_prod:
                return -1
            cursor.execute("SELECT defect_rate FROM material_types WHERE material_type_id = ?;", (material_type_id,))
            row_mat = cursor.fetchone()
            if not row_mat:
                return -1

            coeff = float(row_prod[0])
            defect = float(row_mat[0])
            raw = count * param1 * param2 * coeff * (1.0 + defect / 100.0)
            return math.ceil(raw)
        except Exception:
            return -1
        finally:
            self.close_connection(conn)
