import tkinter as tk
from tkinter import messagebox


class AppDialogs:
    """
    Класс управления интерактивными системными диалоговыми окнами (MessageBox).
    Обеспечивает строгое разделение по типам сообщений и наличие соответствующих пиктограмм.
    """

    @staticmethod
    def show_error(parent, title: str, message: str):
        """
        1. Окно ошибки (Error):
        Вызывается при сбое валидации или недоступности СУБД.
        Содержит пиктограмму ошибки (крестик) и порядок действий по устранению.
        """
        messagebox.showerror(
            title=title,
            message=message,
            parent=parent,
            icon="error"
        )

    @staticmethod
    def ask_warning_discard(parent) -> bool:
        """
        2. Окно предупреждения (Warning):
        Вызывается при нажатии кнопки «Назад» или «Отмена», если данные были изменены.
        Содержит пиктограмму восклицательного знака и предупреждает о потере данных.
        Возвращает True, если пользователь подтверждает выход, иначе False.
        """
        return messagebox.askyesno(
            title="Предупреждение: Несохраненные данные",
            message="Внимание!\n\n"
                    "Вы изменили поля формы. Все внесенные изменения будут безвозвратно утеряны.\n\n"
                    "Вы действительно хотите вернуться назад без сохранения?",
            parent=parent,
            icon="warning"
        )

    @staticmethod
    def show_info_success(parent, title: str, message: str):
        """
        3. Окно информации (Information):
        Вызывается при успешном сохранении партнера в базе данных.
        Содержит пиктограмму инфо-значка (синий значок 'i').
        """
        messagebox.showinfo(
            title=title,
            message=message,
            parent=parent,
            icon="info"
        )
