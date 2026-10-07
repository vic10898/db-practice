# -*- coding: utf-8 -*-
import re


class ValidationError(Exception):
    """Исключение при некорректных данных формы."""

    def __init__(self, message: str, field_name: str = None):
        super().__init__(message)
        self.message = message
        self.field_name = field_name


def validate_partner_form_data(data: dict) -> dict:
    """
    Валидация полей карточки партнера перед записью в БД.
    Ограничения:
    - Наименование не пустое;
    - Email валидного формата и не пустой;
    - Рейтинг строго целое неотрицательное число (>= 0);
    - ИНН корректной длины (10 или 12 цифр, если указан).
    """
    # 1. Наименование партнера
    partner_name = (data.get("partner_name") or "").strip()
    if not partner_name:
        raise ValidationError(
            "Поле «Наименование» обязательно для заполнения.\n\n"
            "Пожалуйста, введите наименование компании или ИП.",
            field_name="partner_name"
        )

    # 2. Email
    email = (data.get("email") or "").strip()
    if not email:
        raise ValidationError(
            "Поле «Email» обязательно для заполнения.\n\n"
            "Пожалуйста, укажите контактный адрес электронной почты.",
            field_name="email"
        )
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError(
            f"Введен некорректный адрес email: «{email}».\n\n"
            "Убедитесь, что адрес содержит символ '@' и доменную зону (например, partner@mail.ru).",
            field_name="email"
        )

    # 3. Рейтинг (строго целое число >= 0)
    raw_rating = str(data.get("rating", "")).strip()
    if not raw_rating:
        cleaned_rating = 0
    else:
        if not raw_rating.isdigit():
            raise ValidationError(
                "Рейтинг должен быть целым неотрицательным числом.\n\n"
                "Пожалуйста, введите положительное целое число или 0 (без знаков, букв и дробей).",
                field_name="rating"
            )
        cleaned_rating = int(raw_rating)
        if cleaned_rating < 0:
            raise ValidationError(
                "Рейтинг не может быть отрицательным числом.\n\n"
                "Пожалуйста, укажите значение 0 или выше.",
                field_name="rating"
            )

    # 4. ИНН (если введен)
    inn = (data.get("inn") or "").strip()
    if inn and not inn.isdigit():
        raise ValidationError(
            "ИНН должен состоять только из цифр.\n\n"
            "Пожалуйста, проверьте правильность введенного ИНН.",
            field_name="inn"
        )

    partner_type = (data.get("partner_type") or "ООО").strip()
    director = (data.get("director") or "").strip()
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()

    return {
        "partner_name": partner_name,
        "partner_type": partner_type,
        "rating": cleaned_rating,
        "director": director,
        "phone": phone,
        "inn": inn or "0000000000",
        "email": email,
        "address": address
    }
