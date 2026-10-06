# -*- coding: utf-8 -*-
import os
import sqlite3
from typing import Optional, Dict, Any

current_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(
    os.path.dirname(current_dir),
    "Инфраструктура данных и ETL (База данных в 3NF)",
    "database.db"
)


class DatabaseManager:
    """Менеджер базы данных для бизнес-логики и расчетов."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or default_db_path
        self._mem_conn = None
        self._init_tables()

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

    def close_connection(self, conn):
        if self.db_path != ":memory:":
            conn.close()

    def _init_tables(self):
        """Создание базовых справочников, если они не существуют."""
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

        # Начальное наполнение типов при отсутствии
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

        conn.commit()
        self.close_connection(conn)

    def get_product_type(self, type_id: int) -> Optional[Dict[str, Any]]:
        """Получение параметров типа продукции по ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_type_id, type_name, coefficient
            FROM product_types
            WHERE product_type_id = ?;
        """, (type_id,))
        row = cursor.fetchone()
        self.close_connection(conn)
        if row:
            return dict(row)
        return None

    def get_material_type(self, type_id: int) -> Optional[Dict[str, Any]]:
        """Получение параметров типа материала по ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT material_type_id, type_name, defect_rate
            FROM material_types
            WHERE material_type_id = ?;
        """, (type_id,))
        row = cursor.fetchone()
        self.close_connection(conn)
        if row:
            return dict(row)
        return None

    def get_partner_total_sales_quantity(self, partner_id: int) -> int:
        """Получение суммарного объема продаж партнера в штуках."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(quantity), 0)
            FROM sales_history
            WHERE partner_id = ?;
        """, (partner_id,))
        res = cursor.fetchone()[0]
        self.close_connection(conn)
        return int(res)
