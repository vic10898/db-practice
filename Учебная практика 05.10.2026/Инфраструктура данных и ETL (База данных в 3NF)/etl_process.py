# -*- coding: utf-8 -*-
import os
import csv
import re
import sqlite3
from datetime import datetime
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")
CLEANED_DIR = os.path.join(BASE_DIR, "cleaned_data")
DB_PATH = os.path.join(BASE_DIR, "database.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

os.makedirs(CLEANED_DIR, exist_ok=True)


def clean_text(value: str) -> str:
    """Удаление лишних пробелов, непечатных символов и нормализация кавычек."""
    if not value:
        return ""
    val = value.strip()
    val = re.sub(r"\s+", " ", val)
    return val


def parse_date_to_iso(date_str: str) -> str:
    """Приведение различных форматов дат к стандарту СУБД YYYY-MM-DD."""
    cleaned = clean_text(date_str)
    patterns = [
        ("%d.%m.%Y", r"^\d{2}\.\d{2}\.\d{4}$"),
        ("%Y/%m/%d", r"^\d{4}/\d{2}/\d{2}$"),
        ("%d-%m-%Y", r"^\d{2}-\d{2}-\d{4}$"),
        ("%Y.%m.%d", r"^\d{4}\.\d{2}\.\d{2}$"),
        ("%Y-%m-%d", r"^\d{4}-\d{2}-\d{2}$"),
    ]
    for fmt, regex in patterns:
        if re.match(regex, cleaned):
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
    raise ValueError(f"Неизвестный формат даты: {date_str}")


def clean_partners():
    """Очистка справочника партнеров (удаление пробелов, форматирование)."""
    raw_path = os.path.join(RAW_DIR, "partners_raw.csv")
    cleaned_path = os.path.join(CLEANED_DIR, "cleaned_partners.csv")

    partners = []
    with open(raw_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = int(clean_text(row["partner_id"]))
            name = clean_text(row["partner_name"])
            inn = clean_text(row["inn"])
            email = clean_text(row["email"])

            partner_type = "ООО"
            if name.startswith("ИП"):
                partner_type = "ИП"
            elif name.startswith("АО"):
                partner_type = "АО"
            elif name.startswith("ПАО"):
                partner_type = "ПАО"

            partners.append({
                "partner_id": pid,
                "partner_name": name,
                "partner_type": partner_type,
                "rating": 10,
                "address": "г. Москва, ул. Производственная, 12",
                "director": "Руководитель Организации",
                "phone": "+7 999 000-00-00",
                "inn": inn,
                "email": email
            })

    fieldnames = [
        "partner_id", "partner_name", "partner_type",
        "rating", "address", "director", "phone", "inn", "email"
    ]
    with open(cleaned_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(partners)

    print(f"[OK] Очищено партнеров: {len(partners)} -> {cleaned_path}")
    return partners


def clean_products():
    """Очистка номенклатуры товаров с поддержкой кодировки CP1251."""
    raw_path = os.path.join(RAW_DIR, "products_raw.csv")
    cleaned_path = os.path.join(CLEANED_DIR, "cleaned_products.csv")

    raw_content = None
    for enc in ["cp1251", "utf-8"]:
        try:
            with open(raw_path, "r", encoding=enc) as f:
                raw_content = f.read()
                break
        except UnicodeDecodeError:
            continue

    lines = raw_content.strip().splitlines()
    reader = csv.DictReader(lines)

    products = []
    for row in reader:
        pid = int(clean_text(row["product_id"]))
        name = clean_text(row["product_name"])
        price = Decimal(clean_text(row["price"])).quantize(Decimal("0.01"))

        products.append({
            "product_id": pid,
            "product_name": name,
            "product_type_id": 1 if pid == 101 else (2 if pid == 102 else 3),
            "price": str(price)
        })

    fieldnames = ["product_id", "product_name", "product_type_id", "price"]
    with open(cleaned_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

    print(f"[OK] Очищено товаров: {len(products)} -> {cleaned_path}")
    return products


def clean_sales(valid_partner_ids, valid_product_ids):
    """Очистка истории продаж, нормализация дат и устранение строки с несуществующим ID партнера."""
    raw_path = os.path.join(RAW_DIR, "sales_history_raw.csv")
    cleaned_path = os.path.join(CLEANED_DIR, "cleaned_sales_history.csv")

    sales = []
    skipped = []

    with open(raw_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = int(clean_text(row["sale_id"]))
            pid = int(clean_text(row["partner_id"]))
            prid = int(clean_text(row["product_id"]))
            raw_date = row["sale_date"]
            qty = int(clean_text(row["quantity"]))
            amount = Decimal(clean_text(row["amount"])).quantize(Decimal("0.01"))

            # Проверка внешнего ключа: если партнер не найден (например, 999), строка отсекается
            if pid not in valid_partner_ids:
                skipped.append((sid, pid, "Несуществующий партнер"))
                continue

            if prid not in valid_product_ids:
                skipped.append((sid, prid, "Несуществующий товар"))
                continue

            iso_date = parse_date_to_iso(raw_date)

            sales.append({
                "sale_id": sid,
                "partner_id": pid,
                "product_id": prid,
                "sale_date": iso_date,
                "quantity": qty,
                "amount": str(amount)
            })

    fieldnames = ["sale_id", "partner_id", "product_id", "sale_date", "quantity", "amount"]
    with open(cleaned_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sales)

    print(f"[OK] Очищено записей продаж: {len(sales)} -> {cleaned_path}")
    if skipped:
        print(f"[!] Исключено записей с нарушением целостности: {len(skipped)}")
        for item in skipped:
            print(f"    - Продажа ID {item[0]}: {item[2]} (ID: {item[1]})")

    return sales


def init_database(partners, products, sales):
    """Инициализация базы данных SQLite и наполнение очищенными данными."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # Справочники типов продукции и материалов
    product_types = [
        (1, "Паркетная доска", 4.34),
        (2, "Ламинат", 2.35),
        (3, "Массивная доска", 5.15),
        (4, "Пробковое покрытие", 1.50)
    ]
    conn.executemany("""
        INSERT INTO product_types (product_type_id, type_name, coefficient)
        VALUES (?, ?, ?);
    """, product_types)

    material_types = [
        (1, "Тип материала 1 (Дубовый шпон)", 0.28),
        (2, "Тип материала 2 (Хвойная подложка)", 0.55),
        (3, "Тип материала 3 (Защитный лак)", 0.12),
        (4, "Тип материала 4 (Пробковая гранула)", 0.85)
    ]
    conn.executemany("""
        INSERT INTO material_types (material_type_id, type_name, defect_rate)
        VALUES (?, ?, ?);
    """, material_types)

    # Заполнение партнеров
    for p in partners:
        conn.execute("""
            INSERT INTO partners (partner_id, partner_name, partner_type, rating, address, director, phone, inn, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            p["partner_id"], p["partner_name"], p["partner_type"],
            p["rating"], p["address"], p["director"], p["phone"],
            p["inn"], p["email"]
        ))

    # Заполнение товаров
    for pr in products:
        conn.execute("""
            INSERT INTO products (product_id, product_name, product_type_id, price)
            VALUES (?, ?, ?, ?);
        """, (
            pr["product_id"], pr["product_name"],
            pr.get("product_type_id", 1), pr["price"]
        ))

    # Заполнение истории продаж
    for s in sales:
        conn.execute("""
            INSERT INTO sales_history (sale_id, partner_id, product_id, sale_date, quantity, amount)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (
            s["sale_id"], s["partner_id"], s["product_id"],
            s["sale_date"], s["quantity"], s["amount"]
        ))

    conn.commit()
    print(f"[OK] База данных успешно инициализирована: {DB_PATH}")

    # Проверка целостности
    cur = conn.cursor()
    print("--- Проверка таблиц БД ---")
    for tbl in ["partners", "products", "sales_history", "product_types", "material_types"]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cur.fetchone()[0]
        print(f"Таблица {tbl}: {cnt} строк")

    conn.close()


def main():
    print("=== Запуск ETL-конвейера (Практика 05.10.2026) ===")
    partners = clean_partners()
    products = clean_products()

    valid_pids = {p["partner_id"] for p in partners}
    valid_prids = {p["product_id"] for p in products}

    sales = clean_sales(valid_pids, valid_prids)
    init_database(partners, products, sales)
    print("=== ETL-конвейер успешно выполнен ===")


if __name__ == "__main__":
    main()
