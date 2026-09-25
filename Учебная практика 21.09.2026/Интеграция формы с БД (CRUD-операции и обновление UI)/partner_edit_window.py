import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

current_dir = os.path.dirname(os.path.abspath(__file__))
from db_manager import DatabaseManager, IntegrityViolationError, PartnerNotFoundError


class StyledButton(tk.Label):
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
    Форма добавления и редактирования партнера с интеграцией с БД.
    Поддерживает режимы INSERT и UPDATE с автоподгрузкой и обновлением UI.
    """

    PARTNER_TYPES = ("ЗАО", "ООО", "ИП", "ПАО", "ОАО")

    def __init__(self, master=None, db_manager: DatabaseManager = None, partner_id: int = None, on_saved_callback=None):
        super().__init__(master)
        self.master = master
        self.db = db_manager or DatabaseManager()
        self.partner_id = partner_id
        self.on_saved_callback = on_saved_callback

        if self.partner_id is None:
            self.title("CRM: Карточка партнера [Создание]")
        else:
            self.title("CRM: Карточка партнера [Редактирование]")

        self.geometry("560x620")
        self.minsize(500, 540)
        self.configure(bg="#F4F6F9")

        self.protocol("WM_DELETE_WINDOW", self.on_back_clicked)

        self._build_header()
        self._build_fields()
        self._build_buttons()

        if self.partner_id is not None:
            self._load_partner_from_db()

        self.transient(master)
        self.grab_set()
        self.focus_set()

    def _build_header(self):
        header_text = (
            "Добавление нового партнера в базу"
            if self.partner_id is None
            else f"Редактирование данных партнера (ID: {self.partner_id})"
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

    def _build_fields(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=28, pady=16)
        container.pack(fill="both", expand=True)

        self._lbl(container, "Наименование компании *:")
        self.entry_name = tk.Entry(container, font=("Arial", 10), bg="#FFFFFF", fg="#111827", insertbackground="#111827", relief="solid", bd=1)
        self.entry_name.pack(fill="x", pady=(0, 8), ipady=4)

        self._lbl(container, "Тип партнера *:")
        self.combo_type = ttk.Combobox(container, values=self.PARTNER_TYPES, state="readonly", font=("Arial", 10))
        self.combo_type.current(1)
        self.combo_type.pack(fill="x", pady=(0, 8), ipady=3)

        self._lbl(container, "Рейтинг (целое неотрицательное число):")
        self.entry_rating = tk.Entry(container, font=("Arial", 10), bg="#FFFFFF", fg="#111827", insertbackground="#111827", relief="solid", bd=1)
        self.entry_rating.insert(0, "0")
        self.entry_rating.pack(fill="x", pady=(0, 8), ipady=4)

        self._lbl(container, "Юридический / фактический адрес:")
        self.entry_address = tk.Entry(container, font=("Arial", 10), bg="#FFFFFF", fg="#111827", insertbackground="#111827", relief="solid", bd=1)
        self.entry_address.pack(fill="x", pady=(0, 8), ipady=4)

        self._lbl(container, "ФИО директора:")
        self.entry_director = tk.Entry(container, font=("Arial", 10), bg="#FFFFFF", fg="#111827", insertbackground="#111827", relief="solid", bd=1)
        self.entry_director.pack(fill="x", pady=(0, 8), ipady=4)

        self._lbl(container, "Контактный телефон:")
        self.entry_phone = PlaceholderEntry(container, placeholder="+7 (999) 000-00-00", font=("Arial", 10))
        self.entry_phone.pack(fill="x", pady=(0, 8), ipady=4)

        self._lbl(container, "Email организации *:")
        self.entry_email = PlaceholderEntry(container, placeholder="info@company.ru", font=("Arial", 10))
        self.entry_email.pack(fill="x", pady=(0, 8), ipady=4)

    def _lbl(self, parent, text):
        lbl = tk.Label(parent, text=text, font=("Arial", 9, "bold"), bg="#F4F6F9", fg="#374151", anchor="w")
        lbl.pack(fill="x", pady=(2, 2))

    def _build_buttons(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        bottom_frame = tk.Frame(self, bg="#FFFFFF", padx=24, pady=12)
        bottom_frame.pack(side="bottom", fill="x")

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

        save_btn = StyledButton(
            bottom_frame,
            text="Сохранить в БД",
            bg="#2A73C6",
            fg="#FFFFFF",
            hover_bg="#1E5BA3",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=6,
            command=self.save_partner
        )
        save_btn.pack(side="right")

    def _load_partner_from_db(self):
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
        except PartnerNotFoundError as err:
            messagebox.showerror("Ошибка", str(err))
            self.on_back_clicked()

    def save_partner(self):
        data = {
            "company_name": self.entry_name.get().strip(),
            "partner_type": self.combo_type.get(),
            "rating": self.entry_rating.get().strip() or "0",
            "address": self.entry_address.get().strip(),
            "director": self.entry_director.get().strip(),
            "contact_phone": self.entry_phone.get_real_value(),
            "email": self.entry_email.get_real_value(),
        }

        try:
            if self.partner_id is None:
                new_id = self.db.add_partner(data)
                messagebox.showinfo("Успех", f"Партнер успешно добавлен (ID: {new_id})")
            else:
                self.db.update_partner(self.partner_id, data)
                messagebox.showinfo("Успех", f"Данные партнера #{self.partner_id} успешно обновлены.")

            if self.on_saved_callback:
                self.on_saved_callback()

            self.on_back_clicked()

        except IntegrityViolationError as err:
            messagebox.showerror("Ошибка целостности данных", str(err))
        except Exception as err:
            messagebox.showerror("Ошибка базы данных", f"Не удалось сохранить запись:\n{err}")

    def on_back_clicked(self):
        self.grab_release()
        self.destroy()
