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
    Включает навигацию, историю продаж и встроенный калькулятор сырья.
    """

    def __init__(self, db_manager: DatabaseManager = None):
        super().__init__()

        self.db = db_manager or DatabaseManager()
        self.edit_window = None
        self.history_window = None
        self.calc_window = None

        self.title("CRM: Реестр партнеров и расчет материалов")
        self.geometry("1060x680")
        self.minsize(900, 540)
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
            font=("Arial", 10),
            rowheight=26
        )
        style.configure(
            "Treeview.Heading",
            background="#F1F5F9",
            foreground="#1E293B",
            font=("Arial", 10, "bold"),
            relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", "#2A73C6")],
            foreground=[("selected", "#FFFFFF")]
        )

    def _build_header(self):
        header = tk.Frame(self, bg="#FFFFFF", height=72, padx=24, pady=12)
        header.pack(side="top", fill="x")
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        if os.path.exists(self.logo_path):
            try:
                pil_logo = Image.open(self.logo_path)
                pil_logo = pil_logo.resize((48, 48), Image.Resampling.LANCZOS)
                logo_img = ImageTk.PhotoImage(pil_logo)
                logo_lbl = tk.Label(header, image=logo_img, bg="#FFFFFF")
                logo_lbl.image = logo_img
                logo_lbl.pack(side="left", padx=(0, 16))
            except Exception:
                pass

        title_box = tk.Frame(header, bg="#FFFFFF")
        title_box.pack(side="left")

        title_lbl = tk.Label(
            title_box,
            text="Реестр партнеров",
            font=("Arial", 16, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            title_box,
            text="Управление контрагентами, история реализации и расчет расхода сырья",
            font=("Arial", 9),
            bg="#FFFFFF",
            fg="#6B7280"
        )
        subtitle_lbl.pack(anchor="w")

        btn_box = tk.Frame(header, bg="#FFFFFF")
        btn_box.pack(side="right")

        # 1. Кнопка вызова калькулятора материалов
        calc_btn = StyledButton(
            btn_box,
            text="Калькулятор материалов",
            bg="#059669",
            fg="#FFFFFF",
            hover_bg="#047857",
            font=("Arial", 10, "bold"),
            padx=14,
            pady=7,
            command=self.open_calculator_window
        )
        calc_btn.pack(side="left", padx=(0, 10))

        # 2. Кнопка истории продаж
        history_btn = StyledButton(
            btn_box,
            text="История продаж",
            bg="#0284C7",
            fg="#FFFFFF",
            hover_bg="#0369A1",
            font=("Arial", 10, "bold"),
            padx=14,
            pady=7,
            command=self.open_history_window
        )
        history_btn.pack(side="left", padx=(0, 10))

        # 3. Кнопка обновления
        refresh_btn = StyledButton(
            btn_box,
            text="Обновить",
            bg="#E2E8F0",
            fg="#1E293B",
            hover_bg="#CBD5E1",
            font=("Arial", 10),
            padx=14,
            pady=7,
            command=self.refresh_partners
        )
        refresh_btn.pack(side="left", padx=(0, 10))

        # 4. Кнопка добавления
        add_btn = StyledButton(
            btn_box,
            text="+ Добавить партнера",
            bg="#2A73C6",
            fg="#FFFFFF",
            hover_bg="#1E5BA3",
            padx=16,
            pady=7,
            command=self.open_add_window
        )
        add_btn.pack(side="left")

    def _build_table(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=24, pady=16)
        container.pack(fill="both", expand=True)

        cols = ("id", "type", "name", "director", "phone", "email", "sales", "discount", "rating")
        self.tree = ttk.Treeview(container, columns=cols, show="headings", height=14)

        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Тип")
        self.tree.heading("name", text="Наименование компании")
        self.tree.heading("director", text="Директор")
        self.tree.heading("phone", text="Телефон")
        self.tree.heading("email", text="Email")
        self.tree.heading("sales", text="Продажи (ед.)")
        self.tree.heading("discount", text="Скидка")
        self.tree.heading("rating", text="Рейтинг")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("type", width=65, anchor="center")
        self.tree.column("name", width=200, anchor="w")
        self.tree.column("director", width=160, anchor="w")
        self.tree.column("phone", width=130, anchor="center")
        self.tree.column("email", width=155, anchor="w")
        self.tree.column("sales", width=95, anchor="e")
        self.tree.column("discount", width=70, anchor="center")
        self.tree.column("rating", width=65, anchor="center")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.on_double_click_row)

    def _build_status_bar(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        status_frame = tk.Frame(self, bg="#FFFFFF", padx=24, pady=8)
        status_frame.pack(side="bottom", fill="x")

        self.status_lbl = tk.Label(
            status_frame,
            text="Инициализация базы данных...",
            font=("Arial", 9),
            bg="#FFFFFF",
            fg="#4B5563"
        )
        self.status_lbl.pack(side="left")

    def refresh_partners(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            partners = self.db.get_all_partners()
            for p in partners:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        p["id"],
                        p["partner_type"],
                        p["company_name"],
                        p["director"],
                        p["contact_phone"],
                        p["email"],
                        f"{p['total_sales']:,}".replace(",", " "),
                        f"{p['discount']}%",
                        p["rating"]
                    )
                )
            self.status_lbl.config(
                text=f"Всего партнеров в базе: {len(partners)} | СУБД: подключено | Синхронизация успешна",
                fg="#059669"
            )
        except DatabaseConnectionError as err:
            self.status_lbl.config(text="СУБД недоступна", fg="#DC2626")
            AppDialogs.show_error(
                parent=self,
                title="Ошибка подключения к СУБД",
                message=str(err)
            )

    def get_selected_partner_id(self):
        selected = self.tree.selection()
        if not selected:
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def open_history_window(self):
        partner_id = self.get_selected_partner_id()
        if partner_id is None:
            AppDialogs.show_warning(
                parent=self,
                title="Выбор контрагента",
                message="Пожалуйста, выберите партнера в таблице для просмотра истории продаж."
            )
            return

        if self.history_window and self.history_window.winfo_exists():
            self.history_window.destroy()

        self.history_window = PartnerHistoryWindow(
            master=self,
            db_manager=self.db,
            partner_id=partner_id
        )

    def open_calculator_window(self):
        """Открытие калькулятора расчета материалов."""
        if self.calc_window and self.calc_window.winfo_exists():
            self.calc_window.lift()
            return

        self.calc_window = MaterialCalculatorWindow(
            master=self,
            db_manager=self.db
        )

    def open_add_window(self):
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        self.edit_window = PartnerEditWindow(
            master=self,
            db_manager=self.db,
            partner_id=None,
            on_saved_callback=self.refresh_partners
        )

    def on_double_click_row(self, event):
        partner_id = self.get_selected_partner_id()
        if partner_id is None:
            return

        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        self.edit_window = PartnerEditWindow(
            master=self,
            db_manager=self.db,
            partner_id=partner_id,
            on_saved_callback=self.refresh_partners
        )


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
