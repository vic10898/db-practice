def calculate_partner_discount(total_quantity: int) -> int:
    """
    Рассчитывает индивидуальный процент скидки партнера
    на основе суммарного объема купленной продукции за весь период.

    Критерии:
    - менее 10 000 ед.      -> 0%
    - от 10 000 до 49 999  -> 5%
    - от 50 000 до 299 999 -> 10%
    - от 300 000 и более   -> 15%

    :param total_quantity: Суммарный объем купленной продукции (целое число >= 0)
    :return: Процент скидки (0, 5, 10 или 15)
    :raises TypeError: Если передан не целочисленный тип
    :raises ValueError: Если объем меньше нуля
    """
    if not isinstance(total_quantity, int) or isinstance(total_quantity, bool):
        raise TypeError("Объем купленной продукции должен быть целым числом.")

    if total_quantity < 0:
        raise ValueError("Объем купленной продукции не может быть отрицательным.")

    if total_quantity < 10000:
        return 0
    elif total_quantity < 50000:
        return 5
    elif total_quantity < 300000:
        return 10
    else:
        return 15


if __name__ == "__main__":
    test_cases = [0, 9999, 10000, 49999, 50000, 299999, 300000, 500000]
    print("Демонстрация расчета скидок для партнеров:")
    print("-" * 45)
    print(f"{"Объем (ед.)":<15} | {"Скидка (%)":<10}")
    print("-" * 45)
    for qty in test_cases:
        discount = calculate_partner_discount(qty)
        print(f"{qty:<15} | {discount}%")
    print("-" * 45)
