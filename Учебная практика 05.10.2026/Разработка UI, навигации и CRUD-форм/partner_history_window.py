# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from db_manager import DatabaseManager, DatabaseConnectionError, PartnerNotFoundError
from dialogs import AppDialogs
from partner_edit_window import StyledButton


class PartnerHistoryWindow(tk.Toplevel):
    """
    Окно отображения детальной истории отгрузок продукции конкретного партнера.
    Включает кнопку «Назад» для возврата к реестру без потери контекста.
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

        partner_title = self.partner_data["partner_name"]
        self.title(f"CRM: История продаж — {partner_title}")
        self.geometry("880x600")
        self.minsize(760, 500)
        self.configure(bg="#F4F6F9")

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
            "History.Treeview",
            background="#FFFFFF",
            foreground="#111827",
            fieldbackground="#FFFFFF",
            font=("Arial", 11),
            rowheight=30
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
        header = tk.Frame(self, bg="#FFFFFF", padx=24, pady=14)
        header.pack(fill="x")
        tk.Frame(self, bg="#E5E7EB", height=1).pack(fill="x")

        # Логотип
        if os.path.exists(self.logo_path):
            try:
                pil_logo = Image.open(self.logo_path)
                logo_img = ImageTk.PhotoImage(pil_logo)
                logo_lbl = tk.Label(header, image=logo_img, bg="#FFFFFF")
                logo_lbl.image = logo_img
                logo_lbl.pack(side="left", padx=(0, 16))
            except Exception:
                pass

        title_box = tk.Frame(header, bg="#FFFFFF")
        title_box.pack(side="left", fill="x", expand=True)

        lbl_title = tk.Label(
            title_box,
            text=f"История реализации: {self.partner_data['partner_name']}",
            font=("Arial", 14, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            title_box,
            text=f"ИНН: {self.partner_data.get('inn', '—')} | Email: {self.partner_data.get('email', '—')}",
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#6B7280"
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

    def _build_summary_card(self):
        card = tk.Frame(self, bg="#F1F5F9", padx=24, pady=10)
        card.pack(fill="x")

        p = self.partner_data
        discount = p.get("discount", 0)
        total_sales = p.get("total_sales", 0)

        info_text = (
            f"Текущая скидка: {discount}%  |  "
            f"Общий объем отгрузок: {total_sales:,} шт.  |  "
            f"Рейтинг: {p.get('rating', 0)}"
        ).replace(",", " ")

        tk.Label(
            card,
            text=info_text,
            font=("Arial", 11, "bold"),
            bg="#F1F5F9",
            fg="#1E40AF"
        ).pack(anchor="w")

    def _build_table(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=24, pady=12)
        container.pack(fill="both", expand=True)

        columns = ("sale_id", "sale_date", "product_name", "quantity", "amount")
        self.tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            style="History.Treeview",
            selectmode="browse"
        )

        self.tree.heading("sale_id", text="№ Продажи")
        self.tree.heading("sale_date", text="Дата реализации")
        self.tree.heading("product_name", text="Наименование продукции")
        self.tree.heading("quantity", text="Количество (шт)")
        self.tree.heading("amount", text="Сумма (руб.)")

        self.tree.column("sale_id", width=100, anchor="center")
        self.tree.column("sale_date", width=140, anchor="center")
        self.tree.column("product_name", width=300, anchor="w")
        self.tree.column("quantity", width=130, anchor="e")
        self.tree.column("amount", width=150, anchor="e")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _build_footer(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(fill="x")
        footer = tk.Frame(self, bg="#FFFFFF", padx=24, pady=12)
        footer.pack(fill="x")

        # Обязательная кнопка «Назад» без потери контекста
        back_btn = StyledButton(
            footer,
            text="← Назад к реестру",
            bg="#E5E7EB",
            fg="#374151",
            hover_bg="#D1D5DB",
            command=self.destroy
        )
        back_btn.pack(side="left")

        self.status_lbl = tk.Label(footer, text="", font=("Arial", 10), bg="#FFFFFF", fg="#6B7280")
        self.status_lbl.pack(side="right")

    def _load_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            sales = self.db.get_partner_sales_history(self.partner_id)
            total_qty = 0
            total_sum = 0.0

            for s in sales:
                qty = s["quantity"]
                amt = float(s["amount"])
                total_qty += qty
                total_sum += amt

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        s["sale_id"],
                        s["sale_date"],
                        s["product_name"],
                        f"{qty:,}".replace(",", " "),
                        f"{amt:,.2f} ₽".replace(",", " ")
                    )
                )

            self.status_lbl.configure(
                text=f"Всего операций: {len(sales)} | Итого: {total_qty} шт. на сумму {total_sum:,.2f} ₽".replace(",", " ")
            )
        except DatabaseConnectionError as err:
            AppDialogs.show_error(self, "Ошибка базы данных", str(err))
