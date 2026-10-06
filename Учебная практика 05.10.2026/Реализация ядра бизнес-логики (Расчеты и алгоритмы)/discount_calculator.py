# -*- coding: utf-8 -*-
from typing import Optional
from db_manager import DatabaseManager


def calculate_partner_discount(sales_volume: int) -> int:
    """
    Расчет процента накопительной скидки партнера
    на основе суммарного объема продаж.
    """
    if sales_volume < 0:
        return 0
    if sales_volume < 10000:
        return 0
    elif sales_volume < 50000:
        return 5
    elif sales_volume < 300000:
        return 10
    else:
        return 15


def get_partner_discount(partner_id: int, db_manager: Optional[DatabaseManager] = None) -> int:
    """
    Получение объема продаж партнера из базы данных
    и расчет индивидуальной скидки.
    """
    if db_manager is None:
        db_manager = DatabaseManager()
    total_sales = db_manager.get_partner_total_sales_quantity(partner_id)
    return calculate_partner_discount(total_sales)
