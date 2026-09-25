import os
import sys
import tkinter as tk
from tkinter import ttk

current_dir = os.path.dirname(os.path.abspath(__file__))
from tooltips import ToolTip


class StyledButton(tk.Label):
    """
    Кроссплатформенная стилизованная кнопка без артефактов отрисовки macOS.
    Гарантирует четкую видимость текста и фона в любой теме оформления.
    """

    def __init__(self, master, text, command=None, bg="#2A73C6", fg="#FFFFFF", hover_bg="#1E5BA3", padx=16, pady=7, font=("Arial", 10, "bold"), **kwargs):
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
    """
    Текстовое поле ввода с поддержкой серого плейсхолдера,
    который исчезает при фокусе и восстанавливается при потере фокуса пустым.
    """

    def __init__(self, master=None, placeholder="", color="#9CA3AF", default_fg="#111827", *args, **kwargs):
        super().__init__(master, bg="#FFFFFF", fg=default_fg, insertbackground=default_fg, relief="solid", bd=1, *args, **kwargs)
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
        """Возвращает фактический текст пользователя без подстановочного плейсхолдера."""
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
    Экранная форма добавления и редактирования партнера.
    Включает строго типизированные поля по ТЗ, маски/подсказки и всплывающие ToolTips.
    """

    PARTNER_TYPES = ("ЗАО", "ООО", "ИП", "ПАО", "ОАО")

    def __init__(self, master=None, partner_id=None, partner_data=None, on_save_callback=None, on_close_callback=None):
        super().__init__(master)
        self.master = master
        self.partner_id = partner_id
        self.initial_data = partner_data or {}
        self.on_save_callback = on_save_callback
        self.on_close_callback = on_close_callback

        # Заголовок строго дифференцирует создание новой карточки и редактирование существующей
        if self.partner_id is None:
            self.title("CRM: Карточка партнера [Создание]")
        else:
            self.title(f"CRM: Карточка партнера [Редактирование]")

        self.geometry("580x640")
        self.minsize(520, 560)
        self.configure(bg="#F4F6F9")

        self.protocol("WM_DELETE_WINDOW", self.on_back_clicked)

        self._build_header()
        self._build_form_fields()
        self._build_action_buttons()

        # Заполнение полей при передаче существующего партнера (режим редактирования)
        if self.partner_id is not None and self.initial_data:
            self._populate_fields(self.initial_data)

        self.transient(master)
        self.grab_set()
        self.focus_set()

    def _build_header(self):
        header_text = (
            "Новый партнер компании"
            if self.partner_id is None
            else f"Редактирование партнера (ID: {self.partner_id})"
        )

        header_frame = tk.Frame(self, bg="#FFFFFF", height=64, padx=24, pady=12)
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

    def _build_form_fields(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=28, pady=18)
        container.pack(fill="both", expand=True)

        # 1. Наименование партнера
        self._create_field_label(container, "Наименование партнера *:")
        self.entry_name = tk.Entry(
            container,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1
        )
        self.entry_name.pack(fill="x", pady=(0, 10), ipady=4)

        # 2. Тип партнера (строго выпадающий список Combobox)
        self._create_field_label(container, "Тип партнера *:")
        # Combobox в режиме readonly исключает ручной ввод некорректной организационно-правовой формы
        self.combo_type = ttk.Combobox(
            container,
            values=self.PARTNER_TYPES,
            state="readonly",
            font=("Arial", 10)
        )
        self.combo_type.current(1)  # По умолчанию выбран "ООО"
        self.combo_type.pack(fill="x", pady=(0, 10), ipady=3)

        # 3. Рейтинг (целое неотрицательное число)
        self._create_field_label(container, "Рейтинг (целое число от 0):")
        self.entry_rating = tk.Entry(
            container,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1
        )
        self.entry_rating.insert(0, "0")
        self.entry_rating.pack(fill="x", pady=(0, 10), ipady=4)

        # 4. Адрес компании
        self._create_field_label(container, "Юридический / фактический адрес:")
        self.entry_address = tk.Entry(
            container,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1
        )
        self.entry_address.pack(fill="x", pady=(0, 10), ipady=4)

        # 5. ФИО директора
        self._create_field_label(container, "ФИО директора компании:")
        self.entry_director = tk.Entry(
            container,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1
        )
        self.entry_director.pack(fill="x", pady=(0, 10), ipady=4)

        # 6. Телефон компании (с плейсхолдером и ToolTip)
        self._create_field_label(container, "Контактный телефон компании:")
        self.entry_phone = PlaceholderEntry(
            container,
            placeholder="+7 (999) 000-00-00",
            font=("Arial", 10)
        )
        self.entry_phone.pack(fill="x", pady=(0, 10), ipady=4)
        ToolTip(self.entry_phone, "Введите номер в формате: +7 (XXX) XXX-XX-XX")

        # 7. Email компании (с плейсхолдером и ToolTip)
        self._create_field_label(container, "Электронная почта (Email) *:")
        self.entry_email = PlaceholderEntry(
            container,
            placeholder="info@company.ru",
            font=("Arial", 10)
        )
        self.entry_email.pack(fill="x", pady=(0, 10), ipady=4)
        ToolTip(self.entry_email, "Обязательное поле. Формат: partner@domain.ru")

    def _create_field_label(self, parent, text: str):
        lbl = tk.Label(
            parent,
            text=text,
            font=("Arial", 9, "bold"),
            bg="#F4F6F9",
            fg="#374151",
            anchor="w"
        )
        lbl.pack(fill="x", pady=(2, 2))
        return lbl

    def _build_action_buttons(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        bottom_frame = tk.Frame(self, bg="#FFFFFF", padx=24, pady=12)
        bottom_frame.pack(side="bottom", fill="x")

        # Кнопка «Назад» / «Отмена»
        cancel_btn = StyledButton(
            bottom_frame,
            text="Назад",
            bg="#E2E8F0",
            fg="#1E293B",
            hover_bg="#CBD5E1",
            font=("Arial", 10),
            padx=18,
            pady=6,
            command=self.on_back_clicked
        )
        cancel_btn.pack(side="left")

        # Кнопка сохранения данных
        save_btn = StyledButton(
            bottom_frame,
            text="Сохранить",
            bg="#2A73C6",
            fg="#FFFFFF",
            hover_bg="#1E5BA3",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=6,
            command=self.on_save_clicked
        )
        save_btn.pack(side="right")

    def _populate_fields(self, data: dict):
        """Автоматическая подгрузка значений при редактировании выбранного партнера."""
        if "company_name" in data:
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, data.get("company_name") or "")

        partner_type = data.get("partner_type") or "ООО"
        if partner_type in self.PARTNER_TYPES:
            self.combo_type.set(partner_type)

        if "rating" in data and data["rating"] is not None:
            self.entry_rating.delete(0, tk.END)
            self.entry_rating.insert(0, str(data["rating"]))

        if "address" in data:
            self.entry_address.delete(0, tk.END)
            self.entry_address.insert(0, data.get("address") or "")

        if "director" in data:
            self.entry_director.delete(0, tk.END)
            self.entry_director.insert(0, data.get("director") or "")

        if "contact_phone" in data:
            self.entry_phone.set_value(data.get("contact_phone") or "")

        if "email" in data:
            self.entry_email.set_value(data.get("email") or "")

    def get_form_data(self) -> dict:
        """Собирает и возвращает нормализованные данные со всех полей формы."""
        return {
            "id": self.partner_id,
            "company_name": self.entry_name.get().strip(),
            "partner_type": self.combo_type.get(),
            "rating": self.entry_rating.get().strip(),
            "address": self.entry_address.get().strip(),
            "director": self.entry_director.get().strip(),
            "contact_phone": self.entry_phone.get_real_value(),
            "email": self.entry_email.get_real_value(),
        }

    def on_save_clicked(self):
        data = self.get_form_data()
        if self.on_save_callback:
            self.on_save_callback(data)
        self.on_back_clicked()

    def on_back_clicked(self):
        self.grab_release()
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()
