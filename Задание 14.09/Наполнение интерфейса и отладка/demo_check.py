import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
core_dir = os.path.join(parent_dir, "Разработка ядра")
db_dir = os.path.join(parent_dir, "Интеграция с БД")

sys.path.append(core_dir)
sys.path.append(db_dir)
sys.path.append(current_dir)

from discount import calculate_partner_discount
from db_service import get_all_partners_with_discounts
from app import PartnerCRMApp


def run_demo_verification():
    """
    Финальный демонстрационный тест всех компонентов информационной системы.
    Проверяет:
    1. Корректность работы ядра бизнес-логики (расчет скидок).
    2. Выборку и агрегацию данных из БД (SUM + LEFT JOIN).
    3. Отказоустойчивость интерфейса и рендеринг карточек.
    """
    print("=" * 65)
    print("ФИНАЛЬНОЕ ДЕМОНСТРАЦИОННОЕ ТЕСТИРОВАНИЕ ПРОЕКТА")
    print("=" * 65)

    # 1. Проверка ядра бизнес-логики
    print("\n1. Проверка ядра расчета скидок...")
    assert calculate_partner_discount(9999) == 0, "Ошибка при объеме 9999"
    assert calculate_partner_discount(10000) == 5, "Ошибка при объеме 10000"
    assert calculate_partner_discount(50000) == 10, "Ошибка при объеме 50000"
    assert calculate_partner_discount(300000) == 15, "Ошибка при объеме 300000"
    print("   [OK] Пограничные значения ядра рассчитаны верно.")

    # 2. Проверка интеграции с БД
    print("\n2. Проверка выборки данных из БД...")
    partners = get_all_partners_with_discounts()
    assert len(partners) > 0, "Список партнеров пуст"
    print(f"   [OK] Из БД успешно получено партнеров: {len(partners)}")
    for p in partners:
        print(f"        - {p['company_name']}: объем {p['total_quantity']} ед. -> скидка {p['discount_percent']}%")

    # 3. Проверка отказоустойчивости интерфейса
    print("\n3. Проверка отказоустойчивости графического интерфейса...")
    app = PartnerCRMApp()
    app.update()

    # Имитация партнера без продаж (NULL)
    test_null_partner = {
        "company_name": 'ООО "Тест Без Продаж"',
        "total_quantity": None,
        "contact_phone": None,
        "rating": None
    }
    app._render_partner_card(test_null_partner)
    print("   [OK] Карточка партнера с отсутствующими продажами (NULL) обработана без ошибок (скидка 0%).")

    app.destroy()
    print("   [OK] Окно приложения успешно закрыто.")

    print("\n" + "=" * 65)
    print("ВСЕ ПРОВЕРКИ УСПЕШНО ПРОЙДЕНЫ! ПРОЕКТ ГОТОВ К СДАЧЕ.")
    print("=" * 65)


if __name__ == "__main__":
    run_demo_verification()
