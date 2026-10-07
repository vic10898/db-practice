# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk

from db_manager import DatabaseManager, DatabaseConnectionError
from dialogs import AppDialogs
from partner_edit_window import StyledButton


class MaterialCalculatorWindow(tk.Toplevel):
    """
    Окно расчета расхода сырья для производства.
    Интегрировано с базой данных и ядром алгоритма расчета.
    """

    def __init__(self, master=None, db_manager: DatabaseManager = None):
        super().__init__(master)
        self.master = master
        self.db = db_manager or DatabaseManager()

        self.title("CRM: Калькулятор расхода сырья")
        self.geometry("620x580")
        self.minsize(560, 520)
        self.configure(bg="#F4F6F9")

        self._build_header()
        self._build_form()
        self._build_footer()

        self._load_combos()

        self.transient(master)
        self.focus_set()

    def _build_header(self):
        header = tk.Frame(self, bg="#FFFFFF", padx=24, pady=16)
        header.pack(fill="x")
        tk.Frame(self, bg="#E5E7EB", height=1).pack(fill="x")

        lbl_title = tk.Label(header, text="Калькулятор расхода материалов", font=("Arial", 14, "bold"), bg="#FFFFFF", fg="#111827")
        lbl_title.pack(anchor="w")

        lbl_desc = tk.Label(header, text="Расчет сырья с учетом параметров продукции, коэффициента и процента брака.", font=("Arial", 10), bg="#FFFFFF", fg="#6B7280")
        lbl_desc.pack(anchor="w", pady=(2, 0))

    def _build_form(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=24, pady=16)
        container.pack(fill="both", expand=True)

        card = tk.Frame(container, bg="#FFFFFF", relief="solid", bd=1, padx=20, pady=16)
        card.pack(fill="both", expand=True)

        # Тип продукции
        tk.Label(card, text="Тип продукции *", font=("Arial", 10, "bold"), bg="#FFFFFF", fg="#374151").pack(anchor="w", pady=(6, 2))
        self.prod_combo = ttk.Combobox(card, state="readonly", font=("Arial", 10))
        self.prod_combo.pack(fill="x", ipady=3)

        # Тип материала
        tk.Label(card, text="Тип материала *", font=("Arial", 10, "bold"), bg="#FFFFFF", fg="#374151").pack(anchor="w", pady=(10, 2))
        self.mat_combo = ttk.Combobox(card, state="readonly", font=("Arial", 10))
        self.mat_combo.pack(fill="x", ipady=3)

        # Количество
        tk.Label(card, text="Количество продукции (шт) *", font=("Arial", 10, "bold"), bg="#FFFFFF", fg="#374151").pack(anchor="w", pady=(10, 2))
        self.count_entry = tk.Entry(card, font=("Arial", 10), relief="solid", bd=1)
        self.count_entry.insert(0, "100")
        self.count_entry.pack(fill="x", ipady=4)

        # Параметр 1
        tk.Label(card, text="Параметр продукции 1 (длина/ширина) *", font=("Arial", 10, "bold"), bg="#FFFFFF", fg="#374151").pack(anchor="w", pady=(10, 2))
        self.p1_entry = tk.Entry(card, font=("Arial", 10), relief="solid", bd=1)
        self.p1_entry.insert(0, "2.0")
        self.p1_entry.pack(fill="x", ipady=4)

        # Параметр 2
        tk.Label(card, text="Параметр продукции 2 (высота/слой) *", font=("Arial", 10, "bold"), bg="#FFFFFF", fg="#374151").pack(anchor="w", pady=(10, 2))
        self.p2_entry = tk.Entry(card, font=("Arial", 10), relief="solid", bd=1)
        self.p2_entry.insert(0, "1.5")
        self.p2_entry.pack(fill="x", ipady=4)

        # Блок результата
        self.res_card = tk.Frame(card, bg="#EFF6FF", relief="solid", bd=1, padx=12, pady=10)
        self.res_card.pack(fill="x", pady=(16, 0))

        self.res_lbl = tk.Label(
            self.res_card,
            text="Итоговый расход сырья: —",
            font=("Arial", 12, "bold"),
            bg="#EFF6FF",
            fg="#1E40AF"
        )
        self.res_lbl.pack(anchor="center")

    def _build_footer(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(fill="x")
        footer = tk.Frame(self, bg="#FFFFFF", padx=24, pady=12)
        footer.pack(fill="x")

        back_btn = StyledButton(
            footer,
            text="← Назад",
            bg="#E5E7EB",
            fg="#374151",
            hover_bg="#D1D5DB",
            command=self.destroy
        )
        back_btn.pack(side="left")

        calc_btn = StyledButton(
            footer,
            text="Рассчитать расход",
            bg="#2A73C6",
            fg="#FFFFFF",
            hover_bg="#1E5BA3",
            command=self.on_calculate
        )
        calc_btn.pack(side="right")

    def _load_combos(self):
        self.prod_types = self.db.get_product_types()
        self.mat_types = self.db.get_material_types()

        self.prod_combo["values"] = [f"{p['product_type_id']}: {p['type_name']} (коэф. {p['coefficient']})" for p in self.prod_types]
        if self.prod_types:
            self.prod_combo.current(0)

        self.mat_combo["values"] = [f"{m['material_type_id']}: {m['type_name']} (брак {m['defect_rate']}%)" for m in self.mat_types]
        if self.mat_types:
            self.mat_combo.current(0)

    def on_calculate(self):
        try:
            prod_idx = self.prod_combo.current()
            mat_idx = self.mat_combo.current()

            if prod_idx < 0 or mat_idx < 0:
                AppDialogs.show_error(self, "Ошибка", "Выберите тип продукции и тип материала.")
                return

            prod_id = self.prod_types[prod_idx]["product_type_id"]
            mat_id = self.mat_types[mat_idx]["material_type_id"]

            count = int(self.count_entry.get().strip())
            p1 = float(self.p1_entry.get().strip().replace(",", "."))
            p2 = float(self.p2_entry.get().strip().replace(",", "."))

            res = self.db.calculate_material(count, prod_id, mat_id, p1, p2)
            if res < 0:
                self.res_lbl.configure(text="Ошибка расчета: некорректные параметры (-1)", fg="#DC2626")
            else:
                self.res_lbl.configure(text=f"Итоговый расход сырья: {res:,} единиц".replace(",", " "), fg="#1E40AF")

        except ValueError:
            AppDialogs.show_error(self, "Ошибка ввода", "Параметры должны быть корректными числами.")
