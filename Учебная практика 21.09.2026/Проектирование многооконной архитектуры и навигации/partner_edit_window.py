import tkinter as tk
from tkinter import ttk


class PartnerEditWindow(tk.Toplevel):
    """
    Окно создания и редактирования партнера.
    Поддерживает динамический заголовок в зависимости от режима (создание/редактирование)
    и безопасное закрытие с возвратом на главное окно.
    """

    def __init__(self, master=None, partner_id=None, on_close_callback=None):
        super().__init__(master)
        self.master = master
        self.partner_id = partner_id
        self.on_close_callback = on_close_callback

        # Индивидуальный заголовок в зависимости от режима работы формы
        if self.partner_id is None:
            self.title("CRM: Карточка партнера [Создание]")
        else:
            self.title("CRM: Карточка партнера [Редактирование]")

        self.geometry("520x460")
        self.minsize(460, 380)
        self.configure(bg="#F4F6F9")

        # Перехват системного закрытия окна (крестик)
        self.protocol("WM_DELETE_WINDOW", self.on_back_clicked)

        self._build_ui()

        # Модальный режим для предотвращения повторного открытия
        self.transient(master)
        self.grab_set()
        self.focus_set()

    def _build_ui(self):
        header_text = (
            "Создание карточки партнера"
            if self.partner_id is None
            else f"Редактирование партнера #{self.partner_id}"
        )

        header_frame = tk.Frame(self, bg="#FFFFFF", height=60, padx=20, pady=12)
        header_frame.pack(side="top", fill="x")

        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        title_lbl = tk.Label(
            header_frame,
            text=header_text,
            font=("Arial", 14, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        title_lbl.pack(side="left")

        content_frame = tk.Frame(self, bg="#F4F6F9", padx=24, pady=20)
        content_frame.pack(fill="both", expand=True)

        info_lbl = tk.Label(
            content_frame,
            text="Форма просмотра и редактирования параметров партнера.\n"
                 "Для возврата в реестр нажмите кнопку «Назад».",
            font=("Arial", 11),
            bg="#F4F6F9",
            fg="#4B5563",
            justify="left"
        )
        info_lbl.pack(anchor="w", pady=(0, 20))

        # Нижняя панель с кнопкой «Назад»
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        bottom_frame = tk.Frame(self, bg="#FFFFFF", padx=20, pady=12)
        bottom_frame.pack(side="bottom", fill="x")

        back_btn = tk.Button(
            bottom_frame,
            text="Назад",
            font=("Arial", 10, "bold"),
            bg="#E5E7EB",
            fg="#1F2937",
            padx=16,
            pady=6,
            command=self.on_back_clicked
        )
        back_btn.pack(side="left")

    def on_back_clicked(self):
        """Закрывает карточку и возвращает управление главному окну."""
        self.grab_release()
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()
