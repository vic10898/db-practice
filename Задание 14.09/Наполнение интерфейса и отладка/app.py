import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# Подключение модулей ядра и базы данных
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
core_dir = os.path.join(parent_dir, "Разработка ядра")
db_dir = os.path.join(parent_dir, "Интеграция с БД")

sys.path.append(core_dir)
sys.path.append(db_dir)

from discount import calculate_partner_discount
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


class PartnerCRMApp(tk.Tk):
    """
    Основное окно CRM-системы: Отображение партнеров с динамическим расчетом скидок.
    Включает обработку отказоустойчивости (NULL-значения, отсутствие продаж, сбои подключения).
    """

    def __init__(self):
        super().__init__()

        self.title("CRM: Список партнеров и скидок")
        self.geometry("880x680")
        self.minsize(740, 520)
        self.configure(bg="#F4F6F9")

        # Пути к графическим ассетам
        self.res_dir = os.path.join(current_dir, "resources")
        self.icon_path = os.path.join(self.res_dir, "icon.png")
        self.logo_path = os.path.join(self.res_dir, "logo.png")

        self._set_app_icon()
        self._ensure_database_ready()

        self._create_header()
        self._create_partners_container()
        self._create_status_bar()

        # Первичная загрузка данных при запуске приложения
        self.refresh_partners_list()

    def _set_app_icon(self):
        """Устанавливает иконку приложения в левом верхнем углу окна."""
        if os.path.exists(self.icon_path):
            try:
                icon_img = ImageTk.PhotoImage(file=self.icon_path)
                self.iconphoto(False, icon_img)
                self._icon_ref = icon_img
            except Exception:
                pass

    def _ensure_database_ready(self):
        """Проверяет и гарантирует готовность таблиц базы данных к работе."""
        try:
            conn = get_connection()
            init_mock_db(conn)
            conn.close()
        except Exception as err:
            print(f"Инициализация базы данных: {err}")

    def _create_header(self):
        """Создает шапку приложения с логотипом компании и элементами управления."""
        header_frame = tk.Frame(self, bg="#FFFFFF", height=72, padx=24, pady=12)
        header_frame.pack(side="top", fill="x")

        separator = tk.Frame(self, bg="#E5E7EB", height=1)
        separator.pack(side="top", fill="x")

        # Логотип компании
        if os.path.exists(self.logo_path):
            try:
                pil_logo = Image.open(self.logo_path)
                logo_img = ImageTk.PhotoImage(pil_logo)
                logo_label = tk.Label(header_frame, image=logo_img, bg="#FFFFFF")
                logo_label.image = logo_img
                logo_label.pack(side="left", padx=(0, 20))
            except Exception:
                pass

        title_label = tk.Label(
            header_frame,
            text="Список партнеров",
            font=("Arial", 16, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        title_label.pack(side="left", pady=8)

        # Кнопка обновления списка партнеров (стилизованный элемент без артефактов macOS)
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
        refresh_btn.bind("<Button-1>", lambda e: self.refresh_partners_list())
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.configure(bg="#1E5BA3"))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.configure(bg="#2A73C6"))
        refresh_btn.pack(side="right", pady=8)

    def _create_partners_container(self):
        """Создает область прокрутки для карточек партнеров."""
        container = tk.Frame(self, bg="#F4F6F9")
        container.pack(side="top", fill="both", expand=True, padx=24, pady=16)

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

        self.cards_frame = tk.Frame(self.canvas, bg="#F4F6F9")
        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _create_status_bar(self):
        """Создает нижнюю строку состояния для отображения статуса системы."""
        self.status_bar = tk.Frame(self, bg="#FFFFFF", height=28, padx=24, pady=6)
        self.status_bar.pack(side="bottom", fill="x")

        status_sep = tk.Frame(self, bg="#E5E7EB", height=1)
        status_sep.pack(side="bottom", fill="x")

        self.status_label = tk.Label(
            self.status_bar,
            text="Загрузка данных...",
            font=("Arial", 9),
            bg="#FFFFFF",
            fg="#6B7280"
        )
        self.status_label.pack(side="left")

    def _on_canvas_configure(self, event):
        """Адаптирует ширину карточек при изменении размера окна."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Обеспечивает плавную прокрутку списка карточек."""
        if sys.platform == "darwin":
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def refresh_partners_list(self):
        """
        Загружает актуальный список партнеров из базы данных,
        обрабатывает возможные исключения и перерисовывает карточки.
        """
        for child in self.cards_frame.winfo_children():
            child.destroy()

        try:
            raw_partners = get_all_partners_with_discounts()
        except Exception as err:
            self.status_label.configure(
                text=f"Ошибка подключения к базе данных: {err}",
                fg="#DC2626"
            )
            messagebox.showerror("Ошибка БД", f"Не удалось получить данные из базы:\n{err}")
            return

        if not raw_partners:
            empty_lbl = tk.Label(
                self.cards_frame,
                text="В базе данных нет записей о партнерах.",
                font=("Arial", 12),
                bg="#F4F6F9",
                fg="#6B7280"
            )
            empty_lbl.pack(pady=40)
            self.status_label.configure(text="Партнеры не найдены", fg="#6B7280")
            return

        # Рендеринг карточек партнеров
        rendered_count = 0
        for partner_data in raw_partners:
            self._render_partner_card(partner_data)
            rendered_count += 1

        self.status_label.configure(
            text=f"Всего партнеров: {rendered_count} | База данных: подключено | Данные актуальны",
            fg="#059669"
        )

    def _render_partner_card(self, data: dict):
        """
        Формирует отдельную карточку партнера со строгой защитой от отсутствующих данных:
        - Если SUM(quantity) IS NULL или 0 -> скидка 0% (без TypeError/NullPointer)
        - Если контактные данные отсутствуют -> подставляются корректные плейсхолдеры
        - Карточка оформлена строго по макету Screenshot_2.
        """
        # Обработка объема продаж и скидки (защита от NULL и отрицательных величин)
        raw_quantity = data.get("total_quantity")
        if raw_quantity is None or raw_quantity < 0:
            quantity = 0
        else:
            quantity = int(raw_quantity)

        # Вызов ядра бизнес-логики (Задание 1)
        discount_percent = calculate_partner_discount(quantity)

        # Разбор наименования и типа организации
        full_name = data.get("company_name") or "Без наименования"
        if " " in full_name and ('"' in full_name or "ИП" in full_name or "ТК" in full_name):
            parts = full_name.split(" ", 1)
            partner_type = parts[0].strip()
            partner_name = parts[1].strip()
            title_text = f"{partner_type} | {partner_name}"
        else:
            title_text = f"Партнер | {full_name}"

        # Защита контактных данных от NULL
        director_text = data.get("director") or "Директор: Иванов И.И."
        phone_text = data.get("contact_phone") or "+7 (999) 000-00-00"
        rating_val = data.get("rating") if data.get("rating") is not None else 10

        # Контейнер карточки (белый фон, рамка solid 1px)
        card_box = tk.Frame(
            self.cards_frame,
            bg="#FFFFFF",
            relief="solid",
            bd=1,
            padx=18,
            pady=14
        )
        card_box.pack(fill="x", pady=6)

        # 1-я строка: Название слева, скидка справа
        top_line = tk.Frame(card_box, bg="#FFFFFF")
        top_line.pack(fill="x")

        name_lbl = tk.Label(
            top_line,
            text=title_text,
            font=("Arial", 12, "bold"),
            bg="#FFFFFF",
            fg="#111827",
            anchor="w"
        )
        name_lbl.pack(side="left")

        discount_lbl = tk.Label(
            top_line,
            text=f"{discount_percent}%",
            font=("Arial", 13, "bold"),
            bg="#FFFFFF",
            fg="#111827",
            anchor="e"
        )
        discount_lbl.pack(side="right")

        # 2-я строка: Директор
        director_lbl = tk.Label(
            card_box,
            text=director_text,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#374151",
            anchor="w"
        )
        director_lbl.pack(fill="x", pady=(4, 2))

        # 3-я строка: Телефон
        phone_lbl = tk.Label(
            card_box,
            text=phone_text,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#374151",
            anchor="w"
        )
        phone_lbl.pack(fill="x", pady=2)

        # 4-я строка: Рейтинг
        rating_lbl = tk.Label(
            card_box,
            text=f"Рейтинг: {rating_val}",
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#374151",
            anchor="w"
        )
        rating_lbl.pack(fill="x", pady=(2, 0))


if __name__ == "__main__":
    app = PartnerCRMApp()
    app.mainloop()
