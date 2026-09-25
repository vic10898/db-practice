import tkinter as tk
from tkinter import messagebox


class CustomWarningDialog(tk.Toplevel):
    """
    Интерактивное диалоговое окно предупреждения с гарантированной поддержкой
    русскоязычных кнопок («Да» / «Отмена») и стилизацией под macOS/Windows.
    """

    def __init__(self, parent, title="Предупреждение: Несохраненные данные", message=None):
        super().__init__(parent)
        self.result = False

        self.title(title)
        self.geometry("460x220")
        self.resizable(False, False)
        self.configure(bg="#FFFFFF")

        # Центрирование относительно родительского окна
        self.transient(parent)
        self.grab_set()

        try:
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 230
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 110
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui(message)
        self.wait_window(self)

    def _build_ui(self, message):
        body_frame = tk.Frame(self, bg="#FFFFFF", padx=20, pady=16)
        body_frame.pack(fill="both", expand=True)

        # Пиктограмма предупреждения
        icon_label = tk.Label(
            body_frame,
            text="⚠️",
            font=("Arial", 32),
            bg="#FFFFFF",
            fg="#D97706"
        )
        icon_label.pack(side="left", anchor="n", padx=(0, 16))

        text_box = tk.Frame(body_frame, bg="#FFFFFF")
        text_box.pack(side="left", fill="both", expand=True)

        heading_lbl = tk.Label(
            text_box,
            text="Внимание! Несохраненные изменения",
            font=("Arial", 11, "bold"),
            bg="#FFFFFF",
            fg="#111827",
            anchor="w"
        )
        heading_lbl.pack(fill="x", pady=(0, 6))

        default_msg = (
            "Вы изменили поля формы. Все внесенные изменения будут безвозвратно утеряны.\n\n"
            "Вы действительно хотите вернуться назад без сохранения?"
        )
        desc_lbl = tk.Label(
            text_box,
            text=message or default_msg,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#4B5563",
            justify="left",
            wraplength=320,
            anchor="w"
        )
        desc_lbl.pack(fill="x")

        # Нижняя панель с кнопками
        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        btn_bar = tk.Frame(self, bg="#F9FAFB", padx=16, pady=12)
        btn_bar.pack(side="bottom", fill="x")

        # Кнопка «Да, выйти без сохранения»
        discard_btn = tk.Label(
            btn_bar,
            text="Да, выйти без сохранения",
            bg="#DC2626",
            fg="#FFFFFF",
            font=("Arial", 9, "bold"),
            padx=14,
            pady=7,
            cursor="hand2"
        )
        discard_btn.bind("<Button-1>", lambda e: self._on_confirm())
        discard_btn.bind("<Enter>", lambda e: discard_btn.configure(bg="#B91C1C"))
        discard_btn.bind("<Leave>", lambda e: discard_btn.configure(bg="#DC2626"))
        discard_btn.pack(side="right", padx=(8, 0))

        # Кнопка «Отмена» (остаться)
        stay_btn = tk.Label(
            btn_bar,
            text="Отмена",
            bg="#E2E8F0",
            fg="#1E293B",
            font=("Arial", 9, "bold"),
            padx=16,
            pady=7,
            cursor="hand2"
        )
        stay_btn.bind("<Button-1>", lambda e: self._on_cancel())
        stay_btn.bind("<Enter>", lambda e: stay_btn.configure(bg="#CBD5E1"))
        stay_btn.bind("<Leave>", lambda e: stay_btn.configure(bg="#E2E8F0"))
        stay_btn.pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_confirm(self):
        self.result = True
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self.result = False
        self.grab_release()
        self.destroy()


class AppDialogs:
    """
    Класс управления интерактивными системными диалоговыми окнами (MessageBox).
    Обеспечивает строгое разделение по типам сообщений и наличие соответствующих пиктограмм.
    """

    @staticmethod
    def show_error(parent, title: str, message: str):
        """
        1. Окно ошибки (Error):
        Вызывается при сбое валидации или недоступности СУБД.
        Содержит пиктограмму ошибки (крестик) и порядок действий по устранению.
        """
        messagebox.showerror(
            title=title,
            message=message,
            parent=parent,
            icon="error"
        )

    @staticmethod
    def ask_warning_discard(parent) -> bool:
        """
        2. Окно предупреждения (Warning):
        Вызывается при нажатии кнопки «Назад» или «Отмена», если данные были изменены.
        Обеспечивает вывод на чистом русском языке с кнопками «Да, выйти» и «Отмена».
        """
        try:
            dlg = CustomWarningDialog(parent)
            return dlg.result
        except Exception:
            return messagebox.askyesno(
                title="Предупреждение: Несохраненные данные",
                message="Внимание!\n\n"
                        "Вы изменили поля формы. Все внесенные изменения будут безвозвратно утеряны.\n\n"
                        "Вы действительно хотите вернуться назад без сохранения?",
                parent=parent,
                icon="warning"
            )

    @staticmethod
    def show_info_success(parent, title: str, message: str):
        """
        3. Окно информации (Information):
        Вызывается при успешном сохранении партнера в базе данных.
        Содержит пиктограмму инфо-значка (синий значок 'i').
        """
        messagebox.showinfo(
            title=title,
            message=message,
            parent=parent,
            icon="info"
        )
