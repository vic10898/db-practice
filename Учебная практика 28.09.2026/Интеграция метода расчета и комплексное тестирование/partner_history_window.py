import os
import sys
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from PIL import Image, ImageTk

from db_manager import DatabaseManager, DatabaseConnectionError, PartnerNotFoundError
from dialogs import AppDialogs


class PartnerHistoryWindow(tk.Toplevel):
    """
    Окно отображения детальной истории отгрузок продукции конкретного партнера.
    Соответствует общему корпоративному руководству по стилю.
    """

    def __init__(self, master=None, db_manager: DatabaseManager = None, partner_id: int = None):
        super().__init__(master)
        self.master = master
        self.db = db_manager or DatabaseManager()
        self.partner_id = partner_id

        # Загрузка данных партнера
        try:
            self.partner_data = self.db.get_partner_by_id(self.partner_id)
        except (DatabaseConnectionError, PartnerNotFoundError) as err:
            AppDialogs.show_error(self.master, "Ошибка", str(err))
            self.destroy()
            return

        partner_title = self.partner_data["company_name"]
        self.title(f"CRM: История реализации продукции — {partner_title}")
        self.geometry("860x600")
        self.minsize(760, 500)
        self.configure(bg="#F4F6F9")

        # Определение путей к ресурсам оформления
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        self.res_dir = os.path.join(parent_dir, "resources")
        self.icon_path = os.path.join(self.res_dir, "icon.png")
        self.logo_path = os.path.join(self.res_dir, "logo.png")

        self._setup_icon()
        self._setup_styles()
        self._build_header()
        self._build_summary_card()
        self._build_table()
        self._build_footer()

        self._load_history()

        self.transient(master)
        self.focus_set()

    def _setup_icon(self):
        """Установка фирменной иконки приложения в заголовок окна."""
        if os.path.exists(self.icon_path):
            try:
                icon_img = ImageTk.PhotoImage(file=self.icon_path)
                self.iconphoto(False, icon_img)
                self._icon_ref = icon_img
            except Exception:
                pass

    def _setup_styles(self):
        """Настройка стилей таблицы в соответствии с корпоративным стилем."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "History.Treeview",
            background="#FFFFFF",
            foreground="#111827",
            fieldbackground="#FFFFFF",
            font=("Arial", 11),
            rowheight=32
        )
        style.configure(
            "History.Treeview.Heading",
            background="#F1F5F9",
            foreground="#1E293B",
            font=("Arial", 11, "bold"),
            relief="flat"
        )
        style.map(
            "History.Treeview",
            background=[("selected", "#2A73C6")],
            foreground=[("selected", "#FFFFFF")]
        )

    def _build_header(self):
        """Формирование шапки окна с логотипом компании и заголовком."""
        header_frame = tk.Frame(self, bg="#FFFFFF", height=76, padx=20, pady=12)
        header_frame.pack(side="top", fill="x")

        # Разделительная полоса
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        # Логотип компании в оригинальном разрешении 1:1 без размытия
        if os.path.exists(self.logo_path):
            try:
                pil_logo = Image.open(self.logo_path)
                logo_img = ImageTk.PhotoImage(pil_logo)
                logo_label = tk.Label(header_frame, image=logo_img, bg="#FFFFFF")
                logo_label.image = logo_img
                logo_label.pack(side="left", padx=(0, 20))
            except Exception:
                pass

        title_box = tk.Frame(header_frame, bg="#FFFFFF")
        title_box.pack(side="left", fill="y")

        header_title = tk.Label(
            title_box,
            text=f"История реализации: {self.partner_data['company_name']}",
            font=("Arial", 16, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        header_title.pack(anchor="w")

        header_sub = tk.Label(
            title_box,
            text=f"Тип: {self.partner_data['partner_type']} | Руководитель: {self.partner_data.get('director', '—')}",
            font=("Arial", 11),
            bg="#FFFFFF",
            fg="#6B7280"
        )
        header_sub.pack(anchor="w")

        # Кнопка возврата в шапке
        close_btn = tk.Label(
            header_frame,
            text="Назад к списку",
            font=("Arial", 11, "bold"),
            bg="#E2E8F0",
            fg="#1E293B",
            padx=16,
            pady=7,
            cursor="hand2"
        )
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(bg="#CBD5E1"))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(bg="#E2E8F0"))
        close_btn.pack(side="right", pady=6)

    def _build_summary_card(self):
        """Информационная карточка с общими показателями эффективности партнера."""
        card_box = tk.Frame(self, bg="#F4F6F9", padx=20, pady=12)
        card_box.pack(fill="x")

        inner_card = tk.Frame(card_box, bg="#FFFFFF", padx=16, pady=10, relief="solid", bd=1)
        inner_card.configure(highlightbackground="#E2E8F0", highlightthickness=1)
        inner_card.pack(fill="x")

        self.summary_lbl = tk.Label(
            inner_card,
            text="Загрузка сводных данных по продажам...",
            font=("Arial", 11),
            bg="#FFFFFF",
            fg="#334155"
        )
        self.summary_lbl.pack(side="left")

    def _build_table(self):
        """Формирование таблицы для отображения отгрузок продукции."""
        container = tk.Frame(self, bg="#F4F6F9", padx=20, pady=4)
        container.pack(fill="both", expand=True)

        cols = ("product", "quantity", "date")
        self.tree = ttk.Treeview(
            container,
            columns=cols,
            show="headings",
            style="History.Treeview"
        )

        # Обязательные поля по ТЗ: Наименование продукции, Количество (шт.), Дата продажи
        self.tree.heading("product", text="Наименование продукции")
        self.tree.heading("quantity", text="Количество (шт.)")
        self.tree.heading("date", text="Дата продажи")

        self.tree.column("product", width=380, anchor="w")
        self.tree.column("quantity", width=140, anchor="e")
        self.tree.column("date", width=160, anchor="center")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _build_footer(self):
        """Подвал окна с итоговой статистикой."""
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        footer_frame = tk.Frame(self, bg="#FFFFFF", padx=20, pady=10)
        footer_frame.pack(side="bottom", fill="x")

        self.footer_lbl = tk.Label(
            footer_frame,
            text="",
            font=("Arial", 11),
            bg="#FFFFFF",
            fg="#4B5563"
        )
        self.footer_lbl.pack(side="left")

    def _format_date(self, raw_date_str: str) -> str:
        """
        Преобразование даты продажи в понятный для человека формат (ДД.ММ.ГГГГ).
        """
        if not raw_date_str:
            return "—"
        try:
            dt = datetime.strptime(raw_date_str.strip(), "%Y-%m-%d")
            months = [
                "января", "февраля", "марта", "апреля", "мая", "июня",
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            # Формат вида: 15 марта 2026 г.
            return f"{dt.day} {months[dt.month - 1]} {dt.year} г."
        except ValueError:
            return raw_date_str

    def _load_history(self):
        """Загрузка истории поставок из базы данных через SQL JOIN."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            history = self.db.get_partner_sales_history(self.partner_id)
            total_qty = 0

            if not history:
                self.tree.insert(
                    "",
                    "end",
                    values=("История отгрузок отсутствует", "—", "—")
                )
                self.summary_lbl.config(
                    text="У данного контрагента пока нет зарегистрированных отгрузок."
                )
                self.footer_lbl.config(text="Записей: 0 | Суммарный объем: 0 шт.")
                return

            for record in history:
                qty = record["quantity"]
                total_qty += qty
                formatted_qty = f"{qty:,} шт.".replace(",", " ")
                human_date = self._format_date(record["delivery_date"])

                self.tree.insert(
                    "",
                    "end",
                    values=(record["product_name"], formatted_qty, human_date)
                )

            formatted_total = f"{total_qty:,}".replace(",", " ")
            self.summary_lbl.config(
                text=f"Всего совершено отгрузок: {len(history)} | Совокупный объем: {formatted_total} шт."
            )
            self.footer_lbl.config(
                text=f"Записей: {len(history)} | Суммарный объем реализации: {formatted_total} шт."
            )

        except DatabaseConnectionError as err:
            AppDialogs.show_error(self, "Ошибка подключения к СУБД", str(err))
            self.summary_lbl.config(
                text="Ошибка при загрузке данных истории из СУБД.",
                fg="#DC2626"
            )
