import math
from db_manager import DatabaseManager


def calculate_material_requirement(
    product_type_id: int,
    material_type_id: int,
    quantity: int,
    param_1: float,
    param_2: float,
    db_manager: DatabaseManager = None
) -> int:
    """
    Расчет необходимого количества сырья (материалов) для производства продукции
    с учетом геометрических параметров, типа изделия и технологического процента брака.

    Возвращает целое число единиц сырья (округление вверх) либо -1 при некорректных данных.
    """
    # 1. Валидация типов входных аргументов
    if not isinstance(product_type_id, int):
        return -1
    if not isinstance(material_type_id, int):
        return -1
    if not isinstance(quantity, int):
        return -1
    if not isinstance(param_1, (int, float)):
        return -1
    if not isinstance(param_2, (int, float)):
        return -1

    # 2. Проверка положительности физических величин и объема
    if quantity <= 0:
        return -1
    if param_1 <= 0.0 or param_2 <= 0.0:
        return -1

    # 3. Получение нормативных коэффициентов из справочников БД
    db = db_manager or DatabaseManager()
    coefficient = db.get_product_type_coefficient(product_type_id)
    if coefficient is None or coefficient <= 0:
        return -1

    defect_rate = db.get_material_defect_rate(material_type_id)
    if defect_rate is None or defect_rate < 0:
        return -1

    # 4. Расчет расхода сырья по установленным технологическим формулам
    unit_consumption = float(param_1) * float(param_2) * float(coefficient)
    net_consumption = unit_consumption * quantity

    # Учет брака материала: чистый объем умножается на (1 + процент / 100)
    scrap_multiplier = 1.0 + (float(defect_rate) / 100.0)
    gross_consumption = net_consumption * scrap_multiplier

    # Округление результата строго в большую сторону согласно ТЗ
    total_required = math.ceil(gross_consumption)

    return int(total_required)
