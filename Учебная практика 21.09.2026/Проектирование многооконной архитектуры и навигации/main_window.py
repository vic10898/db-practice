import os
import sys
import tkinter as tk
from tkinter import ttk

current_dir = os.path.dirname(os.path.abspath(__file__))
from partner_edit_window import PartnerEditWindow


class MainWindow(tk.Tk):
    """
    Главная форма реестра партнеров.
    Реализует навигацию к форме добавления/редактирования партнера без потери состояния.
    """

    def __init__(self):
        super().__init__()

        self.title("CRM: Реестр партнеров")
        self.geometry("860x620")
        self.minsize(720, 480)
        self.configure(bg="#F4F6F9")

        self.edit_window = None

        self._build_header()
        self._build_content()
        self._build_status_bar()

    def _build_header(self):
        header_frame = tk.Frame(self, bg="#FFFFFF", height=70, padx=24, pady=12)
        header_frame.pack(side="top", fill="x")

        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="Реестр партнеров",
            font=("Arial", 16, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        title_lbl.pack(side="left")

        # Кнопка перехода к форме добавления партнера
        add_btn = tk.Button(
            header_frame,
            text="+ Добавить партнера",
            font=("Arial", 10, "bold"),
            bg="#2A73C6",
            fg="#FFFFFF",
            padx=16,
            pady=6,
            command=self.open_add_partner_window
        )
        add_btn.pack(side="right")

    def _build_content(self):
        container = tk.Frame(self, bg="#F4F6F9", padx=24, pady=16)
        container.pack(fill="both", expand=True)

        list_caption = tk.Label(
            container,
            text="Выберите действие: нажмите «+ Добавить партнера» для создания новой записи\n"
                 "или дважды кликните по записи в реестре для перехода к редактированию.",
            font=("Arial", 10),
            bg="#F4F6F9",
            fg="#6B7280",
            justify="left"
        )
        list_caption.pack(anchor="w", pady=(0, 12))

        # Демонстрационный список партнеров в виде таблицы
        columns = ("id", "type", "name", "director", "phone", "rating")
        self.tree = ttk.Treeview(container, columns=columns, show="headings", height=12)

        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Тип")
        self.tree.heading("name", text="Наименование компании")
        self.tree.heading("director", text="Руководитель")
        self.tree.heading("phone", text="Телефон")
        self.tree.heading("rating", text="Рейтинг")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("director", width=180, anchor="w")
        self.tree.column("phone", width=140, anchor="center")
        self.tree.column("rating", width=70, anchor="center")

        sample_data = [
            (1, "ООО", 'Логистик-Экспресс', "Иванов И.И.", "+7 (999) 111-22-33", 10),
            (2, "ИП", 'Петров А.В.', "Петров А.В.", "+7 (999) 222-33-44", 8),
            (3, "ЗАО", 'Быстрый Путь', "Сидоров С.С.", "+7 (812) 555-44-33", 12),
        ]
        for item in sample_data:
            self.tree.insert("", "end", values=item)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_item_double_click)

    def _build_status_bar(self):
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        status_bar = tk.Frame(self, bg="#FFFFFF", padx=24, pady=6)
        status_bar.pack(side="bottom", fill="x")

        self.status_label = tk.Label(
            status_bar,
            text="Готово к работе. Окно: Главное меню реестра",
            font=("Arial", 9),
            bg="#FFFFFF",
            fg="#4B5563"
        )
        self.status_label.pack(side="left")

    def open_add_partner_window(self):
        """Открывает окно в режиме создания новой карточки."""
        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        self.status_label.config(text="Открыта карточка: создание нового партнера")
        self.edit_window = PartnerEditWindow(
            master=self,
            partner_id=None,
            on_close_callback=self.on_edit_window_closed
        )

    def on_item_double_click(self, event):
        """Открывает окно в режиме редактирования выбранного партнера."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item_values = self.tree.item(selected_item[0], "values")
        partner_id = int(item_values[0])

        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        self.status_label.config(text=f"Открыта карточка: редактирование партнера #{partner_id}")
        self.edit_window = PartnerEditWindow(
            master=self,
            partner_id=partner_id,
            on_close_callback=self.on_edit_window_closed
        )

    def on_edit_window_closed(self):
        """Callback возврата на главное окно."""
        self.edit_window = None
        self.status_label.config(text="Возврат в главное окно. Состояние сохранено")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
