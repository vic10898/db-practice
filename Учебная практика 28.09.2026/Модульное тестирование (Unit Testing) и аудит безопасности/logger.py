import os
import sys
import logging
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(current_dir, "app.log")


def setup_logger(log_file=LOG_FILE_PATH) -> logging.Logger:
    """
    Инициализирует и настраивает регистратор событий приложения (логгер).
    Обеспечивает запись даты, времени и текста ошибки в файл app.log.
    """
    logger = logging.getLogger("CRMApplication")
    logger.setLevel(logging.INFO)

    # Очистка ранее установленных обработчиков при повторном вызове
    if logger.hasHandlers():
        logger.handlers.clear()

    # Форматтер: Дата Время [УРОВЕНЬ] Сообщение
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Запись в файл app.log с кодировкой UTF-8
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Вывод в консоль
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


# Глобальный экземпляр логгера для приложения
app_logger = setup_logger()


def log_exception(error_message: str, exc: Exception = None):
    """
    Служебная функция для записи исключений в отчетный лог с временной меткой.
    """
    if exc is not None:
        detailed_msg = f"{error_message} | Ошибка: {type(exc).__name__}: {str(exc)}"
    else:
        detailed_msg = error_message
    app_logger.error(detailed_msg)
