import re


class ValidationError(Exception):
    """Исключение при непрохождении валидации входных данных формы."""

    def __init__(self, message: str, field_name: str = None):
        super().__init__(message)
        self.message = message
        self.field_name = field_name


def validate_partner_form_data(data: dict) -> dict:
    """
    Выполняет комплексную валидацию данных перед отправкой в базу данных.
    В случае некорректных значений выбрасывает ValidationError с инструкцией для пользователя.
    Возвращает очищенный словарь нормализованных данных.
    """
    # 1. Проверка обязательного поля: Наименование компании
    company_name = (data.get("company_name") or "").strip()
    if not company_name:
        raise ValidationError(
            "Поле «Наименование» не может быть пустым.\n\n"
            "Пожалуйста, введите официальное название организации или ИП и повторите попытку.",
            field_name="company_name"
        )

    # 2. Проверка обязательного поля: Email
    email = (data.get("email") or "").strip()
    if not email:
        raise ValidationError(
            "Поле «Email» обязательно для заполнения.\n\n"
            "Пожалуйста, укажите действующий адрес электронной почты компании.",
            field_name="email"
        )

    # Проверка формата email
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError(
            f"Введен некорректный формат email: «{email}».\n\n"
            "Пожалуйста, проверьте наличие символа '@' и доменной зоны (например: info@company.ru).",
            field_name="email"
        )

    # 3. Проверка рейтинга: строго целое неотрицательное число
    raw_rating = str(data.get("rating", "")).strip()
    if not raw_rating:
        cleaned_rating = 0
    else:
        # Проверка на наличие минуса, дробей или посторонних символов
        if not raw_rating.isdigit():
            raise ValidationError(
                "Рейтинг должен быть целым числом от 0.\n\n"
                "Пожалуйста, удалите знаки препинания, пробелы или отрицательные значения и повторите попытку.",
                field_name="rating"
            )
        cleaned_rating = int(raw_rating)
        if cleaned_rating < 0:
            raise ValidationError(
                "Рейтинг должен быть целым числом от 0.\n\n"
                "Значение рейтинга не может быть отрицательным. Укажите число 0 или выше.",
                field_name="rating"
            )

    partner_type = (data.get("partner_type") or "ООО").strip()
    director = (data.get("director") or "").strip()
    contact_phone = (data.get("contact_phone") or "").strip()
    address = (data.get("address") or "").strip()

    return {
        "company_name": company_name,
        "partner_type": partner_type,
        "rating": cleaned_rating,
        "director": director,
        "contact_phone": contact_phone,
        "email": email,
        "address": address
    }
