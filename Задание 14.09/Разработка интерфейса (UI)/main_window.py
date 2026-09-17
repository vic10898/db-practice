import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# Подключение модулей бизнес-логики и базы данных
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
db_dir = os.path.join(parent_dir, "Интеграция с БД")
sys.path.append(db_dir)

from db_service import get_all_partners_with_discounts, get_connection
from test_db_service import init_mock_db


class AutoScrollbar(tk.Scrollbar):
    """
    Полоса прокрутки, которая автоматически скрывается, если весь контент
    помещается на экране, и отображается только при необходимости скролла.
    """

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side="right", fill="y")
        super().set(lo, hi)


class PartnerApp(tk.Tk):
    """
    Главное окно приложения менеджера: Список партнеров и их скидок.
    Оформлено в соответствии с требованиями ТЗ и дизайн-макетом (Screenshot_2).
    """

    def __init__(self):
        super().__init__()

        self.title("CRM: Список партнеров и скидок")
        self.geometry("860x650")
        self.minsize(720, 500)
        self.configure(bg="#F4F6F9")

        # Пути к ресурсам
        self.res_dir = os.path.join(current_dir, "resources")
        self.icon_path = os.path.join(self.res_dir, "icon.png")
        self.logo_path = os.path.join(self.res_dir, "logo.png")

        # Установка иконки приложения
        self._set_app_icon()

        # Инициализация БД перед отображением
        self._init_db()

        # Построение интерфейса
        self._create_header()
        self._create_partners_list()

        # Загрузка данных
        self.load_partners()

    def _set_app_icon(self):
        """Устанавливает уникальную иконку приложения в углу окна."""
        if os.path.exists(self.icon_path):
            try:
                icon_img = ImageTk.PhotoImage(file=self.icon_path)
                self.iconphoto(False, icon_img)
                self._icon_ref = icon_img
            except Exception:
                pass

    def _init_db(self):
        """Гарантирует инициализацию таблиц базы данных."""
        try:
            conn = get_connection()
            init_mock_db(conn)
            conn.close()
        except Exception as err:
            print(f"Предупреждение при инициализации БД: {err}")

    def _create_header(self):
        """Создает шапку с логотипом компании и текстовым заголовком."""
        header_frame = tk.Frame(self, bg="#FFFFFF", height=70, padx=20, pady=10)
        header_frame.pack(side="top", fill="x")

        # Разделительная линия снизу шапки
        separator = tk.Frame(self, bg="#E5E7EB", height=1)
        separator.pack(side="top", fill="x")

        # Отображение логотипа компании
        if os.path.exists(self.logo_path):
            try:
                pil_logo = Image.open(self.logo_path)
                logo_img = ImageTk.PhotoImage(pil_logo)
                logo_label = tk.Label(header_frame, image=logo_img, bg="#FFFFFF")
                logo_label.image = logo_img
                logo_label.pack(side="left", padx=(0, 20))
            except Exception:
                pass

        # Текстовый заголовок страницы
        title_label = tk.Label(
            header_frame,
            text="Список партнеров",
            font=("Arial", 16, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        title_label.pack(side="left", pady=10)

        # Кнопка обновления данных (стилизованная метка без артефактов macOS)
        refresh_btn = tk.Label(
            header_frame,
            text="Обновить данные",
            font=("Arial", 10, "bold"),
            bg="#2A73C6",
            fg="#FFFFFF",
            padx=16,
            pady=7,
            cursor="hand2"
        )
        refresh_btn.bind("<Button-1>", lambda e: self.load_partners())
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.configure(bg="#1E5BA3"))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.configure(bg="#2A73C6"))
        refresh_btn.pack(side="right", pady=10)

    def _create_partners_list(self):
        """Создает прокручиваемую область со списком карточек партнеров."""
        container = tk.Frame(self, bg="#F4F6F9")
        container.pack(side="top", fill="both", expand=True, padx=20, pady=15)

        self.canvas = tk.Canvas(container, bg="#F4F6F9", highlightthickness=0, bd=0)
        self.scrollbar = AutoScrollbar(
            container,
            orient="vertical",
            command=self.canvas.yview,
            bg="#CBD5E1",
            troughcolor="#F4F6F9",
            activebackground="#94A3B8",
            bd=0,
            highlightthickness=0,
            relief="flat",
            width=10
        )

        self.scrollable_frame = tk.Frame(self.canvas, bg="#F4F6F9")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)

        # Привязка скролла колесиком мыши
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        """Растягивает внутренний фрейм карточек по ширине окна."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Плавный скролл списка карточек колесиком мыши."""
        if sys.platform == "darwin":
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_partners(self):
        """Загружает список партнеров из базы данных и строит карточки по макету."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            partners = get_all_partners_with_discounts()
        except Exception as err:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить данные из базы: {err}")
            return

        if not partners:
            empty_lbl = tk.Label(
                self.scrollable_frame,
                text="Список партнеров пуст.",
                font=("Arial", 12),
                bg="#F4F6F9",
                fg="#6B7280"
            )
            empty_lbl.pack(pady=40)
            return

        for partner in partners:
            self._render_partner_card(partner)

    def _render_partner_card(self, partner: dict):
        """
        Отрисовывает отдельную карточку партнера строго по макету Screenshot_2.
        Формат:
        [ Тип | Наименование партнера                     Скидка% ]
        [ Директор                                                ]
        [ +7 223 322 22 32                                        ]
        [ Рейтинг: 10                                             ]
        """
        # Внешняя рамка карточки с границей (solid)
        card_frame = tk.Frame(
            self.scrollable_frame,
            bg="#FFFFFF",
            relief="solid",
            bd=1,
            padx=16,
            pady=14
        )
        card_frame.pack(fill="x", pady=6)

        # Выделение типа компании (ООО, ИП, ТК, ЗАО)
        name_full = partner.get("company_name", "")
        if " " in name_full and ('"' in name_full or "ИП" in name_full or "ТК" in name_full):
            parts = name_full.split(" ", 1)
            partner_type = parts[0].strip()
            partner_title = parts[1].strip()
            header_text = f"{partner_type} | {partner_title}"
        else:
            header_text = f"Партнер | {name_full}"

        discount_val = partner.get("discount_percent", 0)
        phone_val = partner.get("contact_phone") or "+7 (999) 000-00-00"

        # Верхняя строка карточки: Слева название, справа скидка %
        top_row = tk.Frame(card_frame, bg="#FFFFFF")
        top_row.pack(fill="x")

        title_lbl = tk.Label(
            top_row,
            text=header_text,
            font=("Arial", 12, "bold"),
            bg="#FFFFFF",
            fg="#111827",
            anchor="w"
        )
        title_lbl.pack(side="left")

        discount_lbl = tk.Label(
            top_row,
            text=f"{discount_val}%",
            font=("Arial", 13, "bold"),
            bg="#FFFFFF",
            fg="#111827",
            anchor="e"
        )
        discount_lbl.pack(side="right")

        # Вторая строка: Директор
        director_name = partner.get("director") or "Директор: Иванов И.И."
        director_lbl = tk.Label(
            card_frame,
            text=director_name,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#374151",
            anchor="w"
        )
        director_lbl.pack(fill="x", pady=(4, 2))

        # Третья строка: Телефон
        phone_lbl = tk.Label(
            card_frame,
            text=phone_val,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#374151",
            anchor="w"
        )
        phone_lbl.pack(fill="x", pady=2)

        # Четвертая строка: Рейтинг
        rating_val = partner.get("rating") or 10
        rating_lbl = tk.Label(
            card_frame,
            text=f"Рейтинг: {rating_val}",
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#374151",
            anchor="w"
        )
        rating_lbl.pack(fill="x", pady=(2, 0))


if __name__ == "__main__":
    app = PartnerApp()
    app.mainloop()
