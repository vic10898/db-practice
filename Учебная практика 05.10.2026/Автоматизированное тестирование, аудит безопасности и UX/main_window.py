# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

from db_manager import DatabaseManager, DatabaseConnectionError
from dialogs import AppDialogs
from partner_edit_window import PartnerEditWindow, StyledButton
from partner_history_window import PartnerHistoryWindow
from material_calculator_window import MaterialCalculatorWindow


class MainWindow(tk.Tk):
    """
    Главная форма CRM-системы: Реестр партнеров.
    Включает навигацию, историю продаж, форму создания/редактирования
    и синхронизацию базы данных с пользовательским интерфейсом.
    """

    def __init__(self, db_manager: DatabaseManager = None):
        super().__init__()

        self.db = db_manager or DatabaseManager()
        self.edit_window = None
        self.history_window = None
        self.calc_window = None

        self.title("CRM: Реестр партнеров и расчет материалов")
        self.geometry("1120x720")
        self.minsize(960, 560)
        self.configure(bg="#F4F6F9")

        # Ресурсы оформления
        self.res_dir = os.path.join(parent_dir, "resources")
        self.icon_path = os.path.join(self.res_dir, "icon.png")
        self.logo_path = os.path.join(self.res_dir, "logo.png")

        self._setup_icon()
        self._setup_styles()
        self._build_header()
        self._build_table()
        self._build_status_bar()

        self.refresh_partners()

    def _setup_icon(self):
        """Установка значка окна."""
        if os.path.exists(self.icon_path):
            try:
                icon_img = ImageTk.PhotoImage(file=self.icon_path)
                self.iconphoto(False, icon_img)
                self._icon_ref = icon_img
            except Exception:
                pass

    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground="#111827",
            fieldbackground="#FFFFFF",
            font=("Arial", 11),
            rowheight=32
        )
        style.configure(
            "Treeview.Heading",
            background="#F1F5F9",
            foreground="#1E293B",
            font=("Arial", 11, "bold"),
            relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", "#2A73C6")],
            foreground=[("selected", "#FFFFFF")]
        )

    def _build_header(self):
        header = tk.Frame(self, bg="#FFFFFF", height=78, padx=24, pady=12)
        header.pack(side="top", fill="x")
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        # Кнопка добавления нового партнера
        right_header_box = tk.Frame(header, bg="#FFFFFF")
        right_header_box.pack(side="right", padx=(16, 0))

        add_btn = StyledButton(
            right_header_box,
            text="+ Добавить партнера",
            bg="#2A73C6",
            fg="#FFFFFF",
            hover_bg="#1E5BA3",
            font=("Arial", 11, "bold"),
            padx=18,
            pady=8,
            command=self.open_add_window
        )
        add_btn.pack(side="right")

        # Логотип компании
        if os.path.exists(self.logo_path):
            try:
                pil_logo = Image.open(self.logo_path)
                logo_img = ImageTk.PhotoImage(pil_logo)
                logo_lbl = tk.Label(header, image=logo_img, bg="#FFFFFF")
                logo_lbl.image = logo_img
                logo_lbl.pack(side="left", padx=(0, 20))
            except Exception:
                pass

        # Заголовок
        title_box = tk.Frame(header, bg="#FFFFFF")
        title_box.pack(side="left", fill="x", expand=True)

        title_lbl = tk.Label(
            title_box,
            text="Реестр партнеров",
            font=("Arial", 18, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            title_box,
            text="Управление контрагентами, история реализации и расчет расхода сырья",
            font=("Arial", 11),
            bg="#FFFFFF",
            fg="#6B7280"
        )
        subtitle_lbl.pack(anchor="w")

        self._build_toolbar()

    def _build_toolbar(self):
        """Панель быстрых действий над реестром."""
        toolbar = tk.Frame(self, bg="#FFFFFF", padx=24, pady=10)
        toolbar.pack(side="top", fill="x")
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        # Кнопка истории продаж
        history_btn = StyledButton(
            toolbar,
            text="История продаж",
            bg="#0284C7",
            fg="#FFFFFF",
            hover_bg="#0369A1",
            font=("Arial", 11, "bold"),
            padx=16,
            pady=7,
            command=self.open_history_window
        )
        history_btn.pack(side="left", padx=(0, 10))

        # Кнопка редактирования выбранного контрагента
        edit_btn = StyledButton(
            toolbar,
            text="Редактировать",
            bg="#4B5563",
            fg="#FFFFFF",
            hover_bg="#374151",
            font=("Arial", 11),
            padx=16,
            pady=7,
            command=self.open_edit_window
        )
        edit_btn.pack(side="left", padx=(0, 10))

        # Кнопка калькулятора сырья
        calc_btn = StyledButton(
            toolbar,
            text="Калькулятор сырья",
            bg="#10B981",
            fg="#FFFFFF",
            hover_bg="#059669",
            font=("Arial", 11),
            padx=16,
            pady=7,
            command=self.open_calculator_window
        )
        calc_btn.pack(side="left", padx=(0, 10))

        # Поле поиска с параметризацией запроса
        search_box = tk.Frame(toolbar, bg="#FFFFFF")
        search_box.pack(side="right")

        tk.Label(
            search_box,
            text="Поиск:",
            font=("Arial", 11),
            bg="#FFFFFF",
            fg="#4B5563"
        ).pack(side="left", padx=(0, 8))

        self.search_entry = tk.Entry(
            search_box,
            font=("Arial", 11),
            relief="solid",
            bd=1,
            width=24
        )
        self.search_entry.pack(side="left", ipady=3)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_partners())

    def _build_table(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=24, pady=16)
        container.pack(side="top", fill="both", expand=True)

        columns = ("id", "type", "name", "rating", "discount", "email", "phone")
        self.tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Тип")
        self.tree.heading("name", text="Наименование партнера")
        self.tree.heading("rating", text="Рейтинг")
        self.tree.heading("discount", text="Скидка")
        self.tree.heading("email", text="Email")
        self.tree.heading("phone", text="Телефон")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("type", width=80, anchor="center")
        self.tree.column("name", width=280, anchor="w")
        self.tree.column("rating", width=90, anchor="center")
        self.tree.column("discount", width=100, anchor="center")
        self.tree.column("email", width=220, anchor="w")
        self.tree.column("phone", width=170, anchor="center")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.open_edit_window())

    def _build_status_bar(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        self.status_bar = tk.Frame(self, bg="#FFFFFF", padx=24, pady=8)
        self.status_bar.pack(side="bottom", fill="x")

        self.status_label = tk.Label(
            self.status_bar,
            text="Загрузка...",
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#6B7280"
        )
        self.status_label.pack(side="left")

    def _get_selected_partner_id(self):
        selected = self.tree.selection()
        if not selected:
            AppDialogs.show_warning(
                self,
                "Выбор партнера",
                "Пожалуйста, выберите партнера из таблицы для выполнения операции."
            )
            return None
        values = self.tree.item(selected[0], "values")
        return int(values[0])

    def refresh_partners(self):
        """Обновление таблицы партнеров из БД."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        search_text = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""

        try:
            partners = self.db.get_all_partners(search_text)
            for p in partners:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        p["partner_id"],
                        p["partner_type"],
                        p["partner_name"],
                        p["rating"],
                        f"{p['discount']}%",
                        p["email"],
                        p.get("phone", "—")
                    )
                )

            self.status_label.configure(
                text=f"Всего контрагентов в базе: {len(partners)}  |  СУБД подключена: SQLite (3NF)"
            )
        except DatabaseConnectionError as err:
            AppDialogs.show_error(
                self,
                "Ошибка соединения",
                f"Не удалось связаться с базой данных.\n\n{err}"
            )
            self.status_label.configure(text="Сбой соединения с базой данных", fg="#DC2626")

    def open_add_window(self):
        """Открытие формы создания партнера с передачей колбэка синхронизации."""
        PartnerEditWindow(
            master=self,
            db_manager=self.db,
            partner_id=None,
            on_save_callback=self.refresh_partners
        )

    def open_edit_window(self):
        """Открытие формы редактирования выбранного контрагента."""
        partner_id = self._get_selected_partner_id()
        if partner_id is None:
            return
        PartnerEditWindow(
            master=self,
            db_manager=self.db,
            partner_id=partner_id,
            on_save_callback=self.refresh_partners
        )

    def open_history_window(self):
        """Открытие окна истории отгрузок выбранного партнера."""
        partner_id = self._get_selected_partner_id()
        if partner_id is None:
            return
        PartnerHistoryWindow(
            master=self,
            db_manager=self.db,
            partner_id=partner_id
        )

    def open_calculator_window(self):
        """Открытие калькулятора сырья."""
        MaterialCalculatorWindow(
            master=self,
            db_manager=self.db
        )


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
