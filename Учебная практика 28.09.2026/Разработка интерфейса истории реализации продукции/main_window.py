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


class MainWindow(tk.Tk):
    """
    Главная форма CRM-системы: Реестр партнеров.
    Позволяет просматривать контрагентов, скидки, вызывать карточку редактирования
    и переходить к истории реализации продукции выбранного партнера.
    """

    def __init__(self, db_manager: DatabaseManager = None):
        super().__init__()

        self.db = db_manager or DatabaseManager()
        self.edit_window = None
        self.history_window = None

        self.title("CRM: Реестр партнеров")
        self.geometry("1080x720")
        self.minsize(920, 560)
        self.configure(bg="#F4F6F9")

        # Ресурсы графического интерфейса
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
        """Установка значка в шапке главного окна."""
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

        # Кнопка добавления партнера справа в шапке (упаковывается первой)
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

        # Логотип компании в оригинальном разрешении 1:1 без размытия
        if os.path.exists(self.logo_path):
            try:
                pil_logo = Image.open(self.logo_path)
                logo_img = ImageTk.PhotoImage(pil_logo)
                logo_lbl = tk.Label(header, image=logo_img, bg="#FFFFFF")
                logo_lbl.image = logo_img
                logo_lbl.pack(side="left", padx=(0, 20))
            except Exception:
                pass

        # Заголовок реестра
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
            text="Управление базой контрагентов, дисконтными программами и отгрузками",
            font=("Arial", 11),
            bg="#FFFFFF",
            fg="#6B7280"
        )
        subtitle_lbl.pack(anchor="w")

        # Панель быстрых действий над таблицей
        self._build_toolbar()

    def _build_toolbar(self):
        """Панель быстрых действий над реестром партнеров."""
        toolbar = tk.Frame(self, bg="#FFFFFF", padx=24, pady=10)
        toolbar.pack(side="top", fill="x")
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

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
        history_btn.pack(side="left", padx=(0, 12))

        refresh_btn = StyledButton(
            toolbar,
            text="Обновить список",
            bg="#E2E8F0",
            fg="#1E293B",
            hover_bg="#CBD5E1",
            font=("Arial", 11),
            padx=14,
            pady=7,
            command=self.refresh_partners
        )
        refresh_btn.pack(side="left")

        hint_lbl = tk.Label(
            toolbar,
            text="* Выберите партнера в таблице для просмотра детальной истории",
            font=("Arial", 10, "italic"),
            bg="#FFFFFF",
            fg="#64748B"
        )
        hint_lbl.pack(side="right", pady=6)

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

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("type", width=75, anchor="center")
        self.tree.column("name", width=230, anchor="w")
        self.tree.column("director", width=180, anchor="w")
        self.tree.column("phone", width=155, anchor="center")
        self.tree.column("email", width=180, anchor="w")
        self.tree.column("sales", width=110, anchor="e")
        self.tree.column("discount", width=80, anchor="center")
        self.tree.column("rating", width=75, anchor="center")

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
            font=("Arial", 11),
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
        """Возвращает идентификатор выбранного партнера либо None."""
        selected = self.tree.selection()
        if not selected:
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def open_history_window(self):
        """Открытие окна истории отгрузок выбранного партнера."""
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
