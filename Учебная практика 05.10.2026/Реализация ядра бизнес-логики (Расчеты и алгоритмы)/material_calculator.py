# -*- coding: utf-8 -*-
import math
from typing import Optional
from db_manager import DatabaseManager


def calculate_material_requirement(
    count: int,
    product_type_id: int,
    material_type_id: int,
    param1: float,
    param2: float,
    db_manager: Optional[DatabaseManager] = None
) -> int:
    """
    Расчет необходимого количества сырья с учетом брака.
    Формула: ⌈Количество * Параметр1 * Параметр2 * Коэффициент * (1 + Брак/100)⌉

    В случае передачи несуществующих ID или отрицательных параметров
    строго возвращается -1 вместо падения программы.
    """
    # Проверка на отрицательные входные параметры
    if count < 0:
        return -1
    if param1 < 0:
        return -1
    if param2 < 0:
        return -1

    # Инициализация менеджера базы данных при отсутствии
    if db_manager is None:
        db_manager = DatabaseManager()

    try:
        # Запрос коэффициента типа продукции из справочника БД
        product_type = db_manager.get_product_type(product_type_id)
        if product_type is None:
            return -1

        # Запрос процента брака материала из справочника БД
        material_type = db_manager.get_material_type(material_type_id)
        if material_type is None:
            return -1

        coefficient = float(product_type["coefficient"])
        defect_rate = float(material_type["defect_rate"])

        # Проверка корректности коэффициентов
        if coefficient <= 0:
            return -1
        if defect_rate < 0:
            return -1

        # Базовый объем сырья на единицу продукции
        unit_raw = param1 * param2 * coefficient

        # Учет процента брака материала
        defect_multiplier = 1.0 + (defect_rate / 100.0)

        # Суммарный объем с учетом брака
        total_raw = float(count) * unit_raw * defect_multiplier

        # Округление строго вверх до целого значения (math.ceil)
        result = math.ceil(total_raw)
        return int(result)

    except Exception:
        # При любых непредвиденных сбоях возвращаем -1
        return -1
