import os
import sys

# Добавление пути к модулю расчета скидки (Задание 1)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
core_dir = os.path.join(parent_dir, "Разработка ядра")
sys.path.append(core_dir)

from discount import calculate_partner_discount

# Попытка импорта официального native-драйвера PostgreSQL (psycopg2)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    import sqlite3

# Параметры подключения к PostgreSQL (по умолчанию для локального сервера)
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}


def get_connection():
    """
    Создает подключение к базе данных PostgreSQL через native-драйвер psycopg2.
    Если psycopg2 не установлен в системе, используется sqlite3 для автономной работы.
    """
    if HAS_PSYCOPG2:
        return psycopg2.connect(
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            cursor_factory=RealDictCursor
        )
    else:
        db_path = os.path.join(current_dir, "partners.db")
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection


def get_partner_sales_volume(partner_id: int, connection=None) -> int:
    """
    Выполняет SQL-запрос с группировкой (SUM(quantity) и LEFT JOIN),
    чтобы вытащить из таблицы sales_history суммарный объем продаж по конкретному партнеру.
    """
    close_after = False
    if connection is None:
        connection = get_connection()
        close_after = True

    try:
        cursor = connection.cursor()
        param_placeholder = "%s" if HAS_PSYCOPG2 else "?"

        query = f"""
            SELECT 
                COALESCE(SUM(s.quantity), 0) AS total_quantity
            FROM partners p
            LEFT JOIN sales_history s ON p.id = s.partner_id
            WHERE p.id = {param_placeholder}
            GROUP BY p.id;
        """
        cursor.execute(query, (partner_id,))
        row = cursor.fetchone()

        if row is None:
            return 0

        return int(row["total_quantity"])
    finally:
        if close_after:
            connection.close()


def get_partner_with_discount(partner_id: int, connection=None) -> dict:
    """
    Объединяет запрос к БД и функцию расчета скидки.
    На выходе возвращает словарь с данными партнера, дополненный его процентом скидки.
    """
    close_after = False
    if connection is None:
        connection = get_connection()
        close_after = True

    try:
        cursor = connection.cursor()
        param_placeholder = "%s" if HAS_PSYCOPG2 else "?"

        query = f"""
            SELECT 
                p.id,
                p.company_name,
                p.inn,
                p.email,
                p.contact_phone,
                COALESCE(SUM(s.quantity), 0) AS total_quantity
            FROM partners p
            LEFT JOIN sales_history s ON p.id = s.partner_id
            WHERE p.id = {param_placeholder}
            GROUP BY p.id, p.company_name, p.inn, p.email, p.contact_phone;
        """
        cursor.execute(query, (partner_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        total_quantity = int(row["total_quantity"])
        discount_percent = calculate_partner_discount(total_quantity)

        partner_data = {
            "id": row["id"],
            "company_name": row["company_name"],
            "inn": row["inn"],
            "email": row["email"],
            "contact_phone": row["contact_phone"],
            "total_quantity": total_quantity,
            "discount_percent": discount_percent
        }

        return partner_data
    finally:
        if close_after:
            connection.close()


def get_all_partners_with_discounts(connection=None) -> list:
    """
    Возвращает список всех партнеров с агрегированным объемом продаж
    и рассчитанным процентом скидки для каждого.
    """
    close_after = False
    if connection is None:
        connection = get_connection()
        close_after = True

    try:
        cursor = connection.cursor()
        query = """
            SELECT 
                p.id,
                p.company_name,
                p.inn,
                p.email,
                p.contact_phone,
                COALESCE(SUM(s.quantity), 0) AS total_quantity
            FROM partners p
            LEFT JOIN sales_history s ON p.id = s.partner_id
            GROUP BY p.id, p.company_name, p.inn, p.email, p.contact_phone
            ORDER BY p.id ASC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        partners_list = []
        for row in rows:
            total_quantity = int(row["total_quantity"])
            discount_percent = calculate_partner_discount(total_quantity)
            partner_item = {
                "id": row["id"],
                "company_name": row["company_name"],
                "inn": row["inn"],
                "email": row["email"],
                "contact_phone": row["contact_phone"],
                "total_quantity": total_quantity,
                "discount_percent": discount_percent
            }
            partners_list.append(partner_item)

        return partners_list
    finally:
        if close_after:
            connection.close()


if __name__ == "__main__":
    driver_name = "psycopg2 (PostgreSQL)" if HAS_PSYCOPG2 else "sqlite3 (автономный режим)"
    print(f"Используемый драйвер базы данных: {driver_name}")
    print("-" * 75)

    # Если используется автономный режим, гарантируем наличие таблиц
    if not HAS_PSYCOPG2:
        from test_db_service import init_mock_db
        conn = get_connection()
        init_mock_db(conn)
        conn.close()

    partners = get_all_partners_with_discounts()
    print("Результат выполнения запроса и расчета скидок:")
    print(f"{'ID':<4} | {'Компания':<25} | {'Объем (ед.)':<12} | {'Скидка':<8}")
    print("-" * 75)
    for p in partners:
        print(f"{p['id']:<4} | {p['company_name']:<25} | {p['total_quantity']:<12} | {p['discount_percent']}%")
    print("-" * 75)
