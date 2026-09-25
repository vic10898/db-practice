import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

current_dir = os.path.dirname(os.path.abspath(__file__))
from db_manager import DatabaseManager
from partner_edit_window import PartnerEditWindow, StyledButton


class MainWindow(tk.Tk):
    """
    Главная форма CRM: отображение списка партнеров из БД
    с автоматическим обновлением при добавлении и редактировании записей.
    """

    def __init__(self, db_manager=None):
        super().__init__()

        self.db = db_manager or DatabaseManager()
        self.edit_window = None

        self.title("CRM: Реестр партнеров")
        self.geometry("960x660")
        self.minsize(800, 520)
        self.configure(bg="#F4F6F9")

        self._setup_styles()
        self._build_header()
        self._build_table()
        self._build_status_bar()

        self.refresh_partners()

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
        header = tk.Frame(self, bg="#FFFFFF", height=70, padx=24, pady=12)
        header.pack(side="top", fill="x")
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        title = tk.Label(
            header,
            text="Реестр партнеров и скидок",
            font=("Arial", 16, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        title.pack(side="left")

        add_btn = StyledButton(
            header,
            text="+ Добавить партнера",
            bg="#2A73C6",
            fg="#FFFFFF",
            hover_bg="#1E5BA3",
            padx=16,
            pady=7,
            command=self.open_add_dialog
        )
        add_btn.pack(side="right", padx=(10, 0))

        reload_btn = StyledButton(
            header,
            text="Обновить",
            bg="#E2E8F0",
            fg="#1E293B",
            hover_bg="#CBD5E1",
            font=("Arial", 10),
            padx=14,
            pady=7,
            command=self.refresh_partners
        )
        reload_btn.pack(side="right")

    def _build_table(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=24, pady=16)
        container.pack(fill="both", expand=True)

        cols = ("id", "type", "name", "director", "phone", "email", "sales", "discount", "rating")
        self.tree = ttk.Treeview(container, columns=cols, show="headings", height=14)

        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Тип")
        self.tree.heading("name", text="Наименование")
        self.tree.heading("director", text="Директор")
        self.tree.heading("phone", text="Телефон")
        self.tree.heading("email", text="Email")
        self.tree.heading("sales", text="Продажи (ед.)")
        self.tree.heading("discount", text="Скидка")
        self.tree.heading("rating", text="Рейтинг")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("type", width=60, anchor="center")
        self.tree.column("name", width=190, anchor="w")
        self.tree.column("director", width=160, anchor="w")
        self.tree.column("phone", width=130, anchor="center")
        self.tree.column("email", width=150, anchor="w")
        self.tree.column("sales", width=95, anchor="e")
        self.tree.column("discount", width=65, anchor="center")
        self.tree.column("rating", width=65, anchor="center")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.on_double_click_row)

    def _build_status_bar(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        status_frame = tk.Frame(self, bg="#FFFFFF", padx=24, pady=6)
        status_frame.pack(side="bottom", fill="x")

        self.status_lbl = tk.Label(
            status_frame,
            text="Инициализация...",
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
                text=f"Всего партнеров в базе: {len(partners)} | База данных: подключено | Данные синхронизированы",
                fg="#059669"
            )
        except Exception as err:
            self.status_lbl.config(text=f"Ошибка загрузки данных: {err}", fg="#DC2626")

    def open_add_dialog(self):
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
        selected = self.tree.selection()
        if not selected:
            return

        partner_id = int(self.tree.item(selected[0], "values")[0])

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
