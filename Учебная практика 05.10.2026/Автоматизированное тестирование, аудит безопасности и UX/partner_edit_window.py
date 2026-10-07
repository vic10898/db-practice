# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk

from validators import validate_partner_form_data, ValidationError
from dialogs import AppDialogs
from db_manager import (
    DatabaseManager,
    DatabaseConnectionError,
    DatabaseIntegrityError,
    PartnerNotFoundError
)


class StyledButton(tk.Label):
    """Кастомная кнопка со стилями и подсветкой при наведении курсора."""

    def __init__(self, master, text, command=None, bg="#2A73C6", fg="#FFFFFF",
                 hover_bg="#1E5BA3", padx=16, pady=7, font=("Arial", 10, "bold"), **kwargs):
        super().__init__(
            master,
            text=text,
            bg=bg,
            fg=fg,
            padx=padx,
            pady=pady,
            font=font,
            cursor="hand2",
            relief="solid",
            bd=0,
            **kwargs
        )
        self.command = command
        self.default_bg = bg
        self.hover_bg = hover_bg

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self.configure(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.configure(bg=self.default_bg))

    def _on_click(self, event=None):
        if self.command:
            self.command()


class PlaceholderEntry(tk.Entry):
    """Поле ввода с визуальной подсказкой (плейсхолдером)."""

    def __init__(self, master=None, placeholder="", color="#9CA3AF", default_fg="#111827", *args, **kwargs):
        super().__init__(
            master,
            bg="#FFFFFF",
            fg=color,
            insertbackground=default_fg,
            relief="solid",
            bd=1,
            highlightthickness=0,
            *args,
            **kwargs
        )
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg = default_fg
        self._has_placeholder = False

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<KeyPress>", self._on_key_press)

        self._show_placeholder()

    def _show_placeholder(self):
        self.delete(0, tk.END)
        self.insert(0, self.placeholder)
        self.configure(fg=self.placeholder_color)
        self._has_placeholder = True

    def _on_focus_in(self, event=None):
        if self._has_placeholder:
            self.after_idle(lambda: self.icursor(0))

    def _on_key_press(self, event):
        ignore_keys = (
            "Tab", "BackSpace", "Delete", "Shift_L", "Shift_R",
            "Control_L", "Control_R", "Alt_L", "Alt_R", "Meta_L",
            "Meta_R", "Left", "Right", "Up", "Down", "Caps_Lock"
        )
        if event.keysym in ignore_keys:
            return
        if self._has_placeholder:
            self.delete(0, tk.END)
            self.configure(fg=self.default_fg)
            self._has_placeholder = False

    def _on_focus_out(self, event=None):
        if not self.get().strip():
            self._show_placeholder()

    def get_value(self) -> str:
        """Получение реального значения без текста плейсхолдера."""
        if self._has_placeholder:
            return ""
        return self.get().strip()

    def set_value(self, text: str):
        """Программная установка значения в поле ввода."""
        self.delete(0, tk.END)
        if text:
            self.insert(0, str(text))
            self.configure(fg=self.default_fg)
            self._has_placeholder = False
        else:
            self._show_placeholder()


class PartnerEditWindow(tk.Toplevel):
    """
    Окно создания и редактирования контрагента.
    Поддерживает валидацию, плейсхолдеры, кнопку «Назад» с контролем изменений
    и синхронизацию с главной формой.
    """

    def __init__(self, master=None, db_manager: DatabaseManager = None, partner_id: int = None, on_save_callback=None):
        super().__init__(master)
        self.master = master
        self.db = db_manager or DatabaseManager()
        self.partner_id = partner_id
        self.on_save_callback = on_save_callback

        self.is_edit_mode = partner_id is not None
        title_suffix = f"Редактирование [ID: {partner_id}]" if self.is_edit_mode else "Создание"
        self.title(f"CRM: Карточка партнера — {title_suffix}")
        self.geometry("640x700")
        self.minsize(580, 620)
        self.configure(bg="#F4F6F9")

        self.initial_data = {}
        self._build_header()
        self._build_form()
        self._build_footer()

        if self.is_edit_mode:
            self._load_partner_data()
        else:
            self._capture_initial_state()

        self.protocol("WM_DELETE_WINDOW", self.on_back_clicked)
        self.transient(master)
        self.focus_set()

    def _build_header(self):
        header = tk.Frame(self, bg="#FFFFFF", padx=24, pady=16)
        header.pack(fill="x")
        tk.Frame(self, bg="#E5E7EB", height=1).pack(fill="x")

        title_text = "Редактирование реквизитов партнера" if self.is_edit_mode else "Новый партнер компании"
        desc_text = "Измените данные и сохраните карточку контрагента." if self.is_edit_mode else "Заполните форму для регистрации нового контрагента."

        lbl_title = tk.Label(header, text=title_text, font=("Arial", 14, "bold"), bg="#FFFFFF", fg="#111827")
        lbl_title.pack(anchor="w")

        lbl_desc = tk.Label(header, text=desc_text, font=("Arial", 10), bg="#FFFFFF", fg="#6B7280")
        lbl_desc.pack(anchor="w", pady=(2, 0))

    def _build_form(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=24, pady=16)
        container.pack(fill="both", expand=True)

        card = tk.Frame(container, bg="#FFFFFF", relief="solid", bd=1, padx=20, pady=16)
        card.pack(fill="both", expand=True)

        # 1. Наименование
        self.name_entry = self._add_field(card, "Наименование партнера *", "Например: ООО \"Вектор\" или ИП Иванов И.И.")

        # 2. Тип партнера (ComboBox)
        lbl_type = tk.Label(card, text="Тип партнера *", font=("Arial", 10, "bold"), bg="#FFFFFF", fg="#374151")
        lbl_type.pack(anchor="w", pady=(8, 4))
        self.type_combo = ttk.Combobox(card, values=["ООО", "ИП", "АО", "ПАО"], state="readonly", font=("Arial", 10))
        self.type_combo.set("ООО")
        self.type_combo.pack(fill="x", ipady=3)

        # 3. Рейтинг (целое неотрицательное)
        self.rating_entry = self._add_field(card, "Рейтинг контрагента *", "Только целое число от 0 (по умолчанию 0)")
        self.rating_entry.set_value("10")

        # 4. ИНН
        self.inn_entry = self._add_field(card, "ИНН *", "10 или 12 цифр налогового номера")

        # 5. Email
        self.email_entry = self._add_field(card, "Email *", "corporate@domain.ru")

        # 6. Телефон
        self.phone_entry = self._add_field(card, "Контактный телефон", "+7 (999) 000-00-00")

        # 7. Директор
        self.director_entry = self._add_field(card, "ФИО руководителя", "Иванов Иван Иванович")

        # 8. Адрес
        self.address_entry = self._add_field(card, "Юридический адрес", "г. Москва, ул. Производственная, 12")

    def _add_field(self, parent, label_text: str, placeholder: str) -> PlaceholderEntry:
        lbl = tk.Label(parent, text=label_text, font=("Arial", 10, "bold"), bg="#FFFFFF", fg="#374151")
        lbl.pack(anchor="w", pady=(8, 4))
        entry = PlaceholderEntry(parent, placeholder=placeholder, font=("Arial", 10))
        entry.pack(fill="x", ipady=4)
        return entry

    def _build_footer(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(fill="x")
        footer = tk.Frame(self, bg="#FFFFFF", padx=24, pady=14)
        footer.pack(fill="x")

        # Кнопка «Назад»
        back_btn = StyledButton(
            footer,
            text="← Назад",
            bg="#E5E7EB",
            fg="#374151",
            hover_bg="#D1D5DB",
            command=self.on_back_clicked
        )
        back_btn.pack(side="left")

        # Кнопка «Сохранить»
        save_btn = StyledButton(
            footer,
            text="Сохранить",
            bg="#2A73C6",
            fg="#FFFFFF",
            hover_bg="#1E5BA3",
            command=self.on_save_clicked
        )
        save_btn.pack(side="right")

    def _capture_initial_state(self):
        self.initial_data = self._get_current_form_data()

    def _get_current_form_data(self) -> dict:
        return {
            "partner_name": self.name_entry.get_value(),
            "partner_type": self.type_combo.get().strip(),
            "rating": self.rating_entry.get_value(),
            "inn": self.inn_entry.get_value(),
            "email": self.email_entry.get_value(),
            "phone": self.phone_entry.get_value(),
            "director": self.director_entry.get_value(),
            "address": self.address_entry.get_value()
        }

    def _has_unsaved_changes(self) -> bool:
        curr = self._get_current_form_data()
        return curr != self.initial_data

    def _load_partner_data(self):
        try:
            p = self.db.get_partner_by_id(self.partner_id)
            self.name_entry.set_value(p.get("partner_name", ""))
            self.type_combo.set(p.get("partner_type", "ООО"))
            self.rating_entry.set_value(str(p.get("rating", 0)))
            self.inn_entry.set_value(p.get("inn", ""))
            self.email_entry.set_value(p.get("email", ""))
            self.phone_entry.set_value(p.get("phone", ""))
            self.director_entry.set_value(p.get("director", ""))
            self.address_entry.set_value(p.get("address", ""))
            self._capture_initial_state()
        except (DatabaseConnectionError, PartnerNotFoundError) as err:
            AppDialogs.show_error(self, "Ошибка загрузки", str(err))
            self.destroy()

    def on_back_clicked(self):
        """Обработка кнопки «Назад» с контролем несохраненных данных."""
        if self._has_unsaved_changes():
            discard = AppDialogs.confirm_discard(self)
            if not discard:
                return
        self.destroy()

    def on_save_clicked(self):
        """Валидация, сохранение в БД и уведомление родительского окна."""
        raw_data = self._get_current_form_data()

        try:
            clean_data = validate_partner_form_data(raw_data)
        except ValidationError as err:
            AppDialogs.show_error(self, "Ошибка валидации", str(err))
            return

        try:
            if self.is_edit_mode:
                self.db.update_partner(self.partner_id, clean_data)
                AppDialogs.show_info(self, "Успех", "Реквизиты партнера успешно сохранены.")
            else:
                new_id = self.db.add_partner(clean_data)
                AppDialogs.show_info(self, "Успех", f"Партнер успешно добавлен (ID: {new_id}).")

            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()

        except (DatabaseConnectionError, DatabaseIntegrityError) as err:
            AppDialogs.show_error(self, "Ошибка базы данных", str(err))
