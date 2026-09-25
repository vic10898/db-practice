import os
import sys
import tkinter as tk
from tkinter import ttk

current_dir = os.path.dirname(os.path.abspath(__file__))
from validators import validate_partner_form_data, ValidationError
from dialogs import AppDialogs
from db_manager import (
    DatabaseManager,
    DatabaseConnectionError,
    DatabaseIntegrityError,
    PartnerNotFoundError
)


class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="", color="#9CA3AF", default_fg="#111827", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg = default_fg
        self._has_placeholder = False

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)
        self._add_placeholder()

    def _clear_placeholder(self, event=None):
        if self._has_placeholder:
            self.delete(0, tk.END)
            self.configure(fg=self.default_fg)
            self._has_placeholder = False

    def _add_placeholder(self, event=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self.configure(fg=self.placeholder_color)
            self._has_placeholder = True

    def get_real_value(self) -> str:
        if self._has_placeholder:
            return ""
        return self.get().strip()

    def set_value(self, text: str):
        self._clear_placeholder()
        self.delete(0, tk.END)
        if text:
            self.insert(0, text)
            self.configure(fg=self.default_fg)
            self._has_placeholder = False
        else:
            self._add_placeholder()


class PartnerEditWindow(tk.Toplevel):
    """
    Экранная форма карточки партнера с валидацией входных данных,
    интерактивными диалоговыми окнами и защитой от потери несохраненных данных.
    """

    PARTNER_TYPES = ("ЗАО", "ООО", "ИП", "ПАО", "ОАО")

    def __init__(self, master=None, db_manager: DatabaseManager = None, partner_id: int = None, on_saved_callback=None):
        super().__init__(master)
        self.master = master
        self.db = db_manager or DatabaseManager()
        self.partner_id = partner_id
        self.on_saved_callback = on_saved_callback

        # Заголовки окон строго отражают назначение
        if self.partner_id is None:
            self.title("CRM: Карточка партнера [Создание]")
        else:
            self.title("CRM: Карточка партнера [Редактирование]")

        self.geometry("560x640")
        self.minsize(500, 560)
        self.configure(bg="#F4F6F9")

        # Перехват кнопки закрытия окна для проверки несохраненных изменений
        self.protocol("WM_DELETE_WINDOW", self.on_back_clicked)

        self._build_header()
        self._build_form()
        self._build_buttons()

        # Загрузка данных при редактировании
        if self.partner_id is not None:
            self._load_partner_data()

        # Фиксируем исходное состояние формы для отслеживания изменений (is_dirty)
        self._initial_state = self.get_raw_form_data()

        self.transient(master)
        self.grab_set()
        self.focus_set()

    def _build_header(self):
        header_text = (
            "Создание нового партнера"
            if self.partner_id is None
            else f"Карточка партнера #{self.partner_id}"
        )

        header_frame = tk.Frame(self, bg="#FFFFFF", height=60, padx=24, pady=12)
        header_frame.pack(side="top", fill="x")
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        title_lbl = tk.Label(
            header_frame,
            text=header_text,
            font=("Arial", 14, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        title_lbl.pack(side="left")

    def _build_form(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=28, pady=16)
        container.pack(fill="both", expand=True)

        self._label(container, "Наименование организации *:")
        self.entry_name = tk.Entry(container, font=("Arial", 10), bg="#FFFFFF", relief="solid", bd=1)
        self.entry_name.pack(fill="x", pady=(0, 8), ipady=4)

        self._label(container, "Организационно-правовая форма (Тип) *:")
        self.combo_type = ttk.Combobox(container, values=self.PARTNER_TYPES, state="readonly", font=("Arial", 10))
        self.combo_type.current(1)
        self.combo_type.pack(fill="x", pady=(0, 8), ipady=3)

        self._label(container, "Рейтинг (целое неотрицательное число от 0) *:")
        self.entry_rating = tk.Entry(container, font=("Arial", 10), bg="#FFFFFF", relief="solid", bd=1)
        self.entry_rating.insert(0, "0")
        self.entry_rating.pack(fill="x", pady=(0, 8), ipady=4)

        self._label(container, "Адрес компании:")
        self.entry_address = tk.Entry(container, font=("Arial", 10), bg="#FFFFFF", relief="solid", bd=1)
        self.entry_address.pack(fill="x", pady=(0, 8), ipady=4)

        self._label(container, "ФИО руководителя компании:")
        self.entry_director = tk.Entry(container, font=("Arial", 10), bg="#FFFFFF", relief="solid", bd=1)
        self.entry_director.pack(fill="x", pady=(0, 8), ipady=4)

        self._label(container, "Контактный телефон:")
        self.entry_phone = PlaceholderEntry(container, placeholder="+7 (999) 000-00-00", font=("Arial", 10), bg="#FFFFFF", relief="solid", bd=1)
        self.entry_phone.pack(fill="x", pady=(0, 8), ipady=4)

        self._label(container, "Email для связи *:")
        self.entry_email = PlaceholderEntry(container, placeholder="info@company.ru", font=("Arial", 10), bg="#FFFFFF", relief="solid", bd=1)
        self.entry_email.pack(fill="x", pady=(0, 8), ipady=4)

    def _label(self, parent, text):
        lbl = tk.Label(parent, text=text, font=("Arial", 9, "bold"), bg="#F4F6F9", fg="#374151", anchor="w")
        lbl.pack(fill="x", pady=(2, 2))

    def _build_buttons(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        bottom_frame = tk.Frame(self, bg="#FFFFFF", padx=24, pady=12)
        bottom_frame.pack(side="bottom", fill="x")

        cancel_btn = tk.Button(
            bottom_frame,
            text="Назад",
            font=("Arial", 10),
            bg="#E5E7EB",
            fg="#1F2937",
            padx=18,
            pady=6,
            command=self.on_back_clicked
        )
        cancel_btn.pack(side="left")

        save_btn = tk.Button(
            bottom_frame,
            text="Сохранить",
            font=("Arial", 10, "bold"),
            bg="#2A73C6",
            fg="#FFFFFF",
            padx=22,
            pady=6,
            command=self.save_data
        )
        save_btn.pack(side="right")

    def _load_partner_data(self):
        try:
            partner = self.db.get_partner_by_id(self.partner_id)
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, partner["company_name"])

            if partner.get("partner_type") in self.PARTNER_TYPES:
                self.combo_type.set(partner["partner_type"])

            self.entry_rating.delete(0, tk.END)
            self.entry_rating.insert(0, str(partner.get("rating", 0)))

            self.entry_address.delete(0, tk.END)
            self.entry_address.insert(0, partner.get("address") or "")

            self.entry_director.delete(0, tk.END)
            self.entry_director.insert(0, partner.get("director") or "")

            self.entry_phone.set_value(partner.get("contact_phone") or "")
            self.entry_email.set_value(partner.get("email") or "")
        except (DatabaseConnectionError, PartnerNotFoundError) as err:
            AppDialogs.show_error(self, "Ошибка загрузки", str(err))
            self.on_force_close()

    def get_raw_form_data(self) -> dict:
        """Считывает сырые данные формы для проверки изменений."""
        return {
            "company_name": self.entry_name.get().strip(),
            "partner_type": self.combo_type.get(),
            "rating": self.entry_rating.get().strip(),
            "address": self.entry_address.get().strip(),
            "director": self.entry_director.get().strip(),
            "contact_phone": self.entry_phone.get_real_value(),
            "email": self.entry_email.get_real_value(),
        }

    def is_dirty(self) -> bool:
        """Проверяет, изменил ли пользователь какие-либо данные с момента открытия."""
        current_state = self.get_raw_form_data()
        return current_state != self._initial_state

    def save_data(self):
        """
        Выполняет валидацию и сохранение в БД с выводом системных MessageBox.
        """
        raw_data = self.get_raw_form_data()

        # Валидация входных данных через конструкцию try...except
        try:
            validated_data = validate_partner_form_data(raw_data)
        except ValidationError as err:
            # 1. Диалоговое окно: Ошибка (Error) с понятным текстом и порядком действий
            AppDialogs.show_error(
                parent=self,
                title="Ошибка валидации данных",
                message=err.message
            )
            # Перевод фокуса на проблемное поле
            if err.field_name == "company_name":
                self.entry_name.focus_set()
            elif err.field_name == "email":
                self.entry_email.focus_set()
            elif err.field_name == "rating":
                self.entry_rating.focus_set()
            return

        # Сохранение в базу данных с перехватом исключений СУБД
        try:
            if self.partner_id is None:
                new_id = self.db.add_partner(validated_data)
                # 3. Диалоговое окно: Информация (Information) об успешном добавлении
                AppDialogs.show_info_success(
                    parent=self,
                    title="Успешное добавление",
                    message=f"Партнер «{validated_data['company_name']}» успешно добавлен в базу данных (ID: {new_id})."
                )
            else:
                self.db.update_partner(self.partner_id, validated_data)
                # 3. Диалоговое окно: Информация (Information) об успешном обновлении
                AppDialogs.show_info_success(
                    parent=self,
                    title="Успешное сохранение",
                    message=f"Данные партнера #{self.partner_id} успешно обновлены в базе данных."
                )

            # Оповещение главного окна об изменении данных
            if self.on_saved_callback:
                self.on_saved_callback()

            self.on_force_close()

        except (DatabaseIntegrityError, DatabaseConnectionError) as err:
            # 1. Диалоговое окно: Ошибка (Error) при сбое СУБД
            AppDialogs.show_error(
                parent=self,
                title="Ошибка базы данных",
                message=str(err)
            )
        except Exception as err:
            AppDialogs.show_error(
                parent=self,
                title="Критическая ошибка",
                message=f"Произошел непредвиденный сбой при сохранении:\n{err}"
            )

    def on_back_clicked(self):
        """
        При нажатии «Назад» / «Отмена» или крестика:
        если пользователь изменил поля, предупреждаем о потере данных.
        """
        if self.is_dirty():
            # 2. Диалоговое окно: Предупреждение (Warning)
            confirmed = AppDialogs.ask_warning_discard(parent=self)
            if not confirmed:
                return

        self.on_force_close()

    def on_force_close(self):
        self.grab_release()
        self.destroy()
