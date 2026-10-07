# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox


class CustomDiscardDialog(tk.Toplevel):
    """
    Интерактивное диалоговое окно предупреждения о потере несохраненных данных
    с явными кнопками «Да» и «Отмена».
    """

    def __init__(self, parent, title="Предупреждение: Несохраненные данные", message=None):
        super().__init__(parent)
        self.result = False

        self.title(title)
        self.geometry("460x220")
        self.resizable(False, False)
        self.configure(bg="#FFFFFF")

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

        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="bottom", fill="x")
        btn_bar = tk.Frame(self, bg="#F9FAFB", padx=16, pady=12)
        btn_bar.pack(side="bottom", fill="x")

        cancel_btn = tk.Button(
            btn_bar,
            text="Отмена (остаться)",
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#374151",
            relief="solid",
            bd=1,
            padx=14,
            pady=6,
            command=self._on_cancel
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        confirm_btn = tk.Button(
            btn_bar,
            text="Да, выйти",
            font=("Arial", 10, "bold"),
            bg="#DC2626",
            fg="#FFFFFF",
            relief="solid",
            bd=0,
            padx=14,
            pady=6,
            command=self._on_confirm
        )
        confirm_btn.pack(side="right")

    def _on_confirm(self):
        self.result = True
        self.destroy()

    def _on_cancel(self):
        self.result = False
        self.destroy()


class AppDialogs:
    """Унифицированный сервис всплывающих диалоговых окон и MessageBox."""

    @staticmethod
    def show_error(parent, title: str, message: str):
        messagebox.showerror(title, message, parent=parent)

    @staticmethod
    def show_warning(parent, title: str, message: str):
        messagebox.showwarning(title, message, parent=parent)

    @staticmethod
    def show_info(parent, title: str, message: str):
        messagebox.showinfo(title, message, parent=parent)

    @staticmethod
    def confirm_discard(parent, message: str = None) -> bool:
        """Диалог подтверждения отмены изменений при закрытии/возврате назад."""
        dialog = CustomDiscardDialog(parent, message=message)
        return dialog.result
