import os
import sys
import tkinter as tk
from tkinter import ttk

current_dir = os.path.dirname(os.path.abspath(__file__))
from partner_edit_window import PartnerEditWindow, StyledButton


class MainWindow(tk.Tk):
    """
    Главная форма со списком партнеров и интеграцией формы ввода.
    """

    def __init__(self):
        super().__init__()

        self.title("CRM: Реестр партнеров")
        self.geometry("900x640")
        self.minsize(740, 500)
        self.configure(bg="#F4F6F9")

        self.edit_window = None

        self.partners_data = [
            {
                "id": 1,
                "company_name": "Логистик-Экспресс",
                "partner_type": "ООО",
                "rating": 10,
                "address": "г. Москва, ул. Ленина, д. 15",
                "director": "Иванов Иван Иванович",
                "contact_phone": "+7 (999) 111-22-33",
                "email": "info@logex.ru"
            },
            {
                "id": 2,
                "company_name": "Петров А.В.",
                "partner_type": "ИП",
                "rating": 8,
                "address": "г. Санкт-Петербург, Невский пр., д. 40",
                "director": "Петров Алексей Владимирович",
                "contact_phone": "+7 (999) 222-33-44",
                "email": "petrov@mail.ru"
            },
            {
                "id": 3,
                "company_name": "Быстрый Путь",
                "partner_type": "ЗАО",
                "rating": 12,
                "address": "г. Казань, ул. Баумана, д. 20",
                "director": "Сидоров Сергей Сергеевич",
                "contact_phone": "+7 (812) 555-44-33",
                "email": "speedway@yandex.ru"
            }
        ]

        self._setup_styles()
        self._build_header()
        self._build_table()
        self._build_status_bar()
        self._refresh_table()

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
        header = tk.Frame(self, bg="#FFFFFF", height=68, padx=24, pady=12)
        header.pack(side="top", fill="x")

        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        title = tk.Label(
            header,
            text="Реестр партнеров организации",
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
            command=self.open_add_window
        )
        add_btn.pack(side="right")

    def _build_table(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=24, pady=16)
        container.pack(fill="both", expand=True)

        cols = ("id", "type", "name", "director", "phone", "email", "rating")
        self.tree = ttk.Treeview(container, columns=cols, show="headings", height=12)

        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Тип")
        self.tree.heading("name", text="Наименование")
        self.tree.heading("director", text="Директор")
        self.tree.heading("phone", text="Телефон")
        self.tree.heading("email", text="Email")
        self.tree.heading("rating", text="Рейтинг")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("name", width=200, anchor="w")
        self.tree.column("director", width=180, anchor="w")
        self.tree.column("phone", width=140, anchor="center")
        self.tree.column("email", width=160, anchor="w")
        self.tree.column("rating", width=60, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)

    def _build_status_bar(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        status_frame = tk.Frame(self, bg="#FFFFFF", padx=24, pady=6)
        status_frame.pack(side="bottom", fill="x")

        self.status_lbl = tk.Label(
            status_frame,
            text="Записей в реестре: 3",
            font=("Arial", 9),
            bg="#FFFFFF",
            fg="#4B5563"
        )
        self.status_lbl.pack(side="left")

    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for p in self.partners_data:
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
                    p["rating"]
                )
            )
        self.status_lbl.config(text=f"Записей в реестре: {len(self.partners_data)}")

    def open_add_window(self):
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        self.edit_window = PartnerEditWindow(
            master=self,
            partner_id=None,
            on_save_callback=self.on_partner_added,
            on_close_callback=lambda: setattr(self, "edit_window", None)
        )

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item_id = int(self.tree.item(selected[0], "values")[0])
        partner = next((p for p in self.partners_data if p["id"] == item_id), None)
        if not partner:
            return

        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        self.edit_window = PartnerEditWindow(
            master=self,
            partner_id=item_id,
            partner_data=partner,
            on_save_callback=self.on_partner_updated,
            on_close_callback=lambda: setattr(self, "edit_window", None)
        )

    def on_partner_added(self, data: dict):
        new_id = max((p["id"] for p in self.partners_data), default=0) + 1
        data["id"] = new_id
        self.partners_data.append(data)
        self._refresh_table()

    def on_partner_updated(self, data: dict):
        for idx, p in enumerate(self.partners_data):
            if p["id"] == data["id"]:
                self.partners_data[idx] = data
                break
        self._refresh_table()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
