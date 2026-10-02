import os
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from db_manager import DatabaseManager, DatabaseConnectionError
from dialogs import AppDialogs
from material_calculator import calculate_material_requirement
from partner_edit_window import StyledButton


class MaterialCalculatorWindow(tk.Toplevel):
    """
    Экранная форма расчета потребности в сырье (материалах) для производства.
    Обеспечивает интерактивный ввод параметров, валидацию и отображение результата.
    """

    def __init__(self, master=None, db_manager: DatabaseManager = None):
        super().__init__(master)
        self.master = master
        self.db = db_manager or DatabaseManager()

        self.title("CRM: Калькулятор расхода материалов")
        self.geometry("620x680")
        self.minsize(560, 600)
        self.configure(bg="#F4F6F9")

        # Каталог графических ресурсов оформления
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        self.res_dir = os.path.join(parent_dir, "resources")
        self.icon_path = os.path.join(self.res_dir, "icon.png")
        self.logo_path = os.path.join(self.res_dir, "logo.png")

        self.product_types_map = {}
        self.material_types_map = {}

        self._setup_icon()
        self._build_header()
        self._build_form()
        self._build_result_panel()
        self._load_reference_data()

        self.transient(master)
        self.focus_set()

    def _setup_icon(self):
        """Установка значка в заголовок окна."""
        if os.path.exists(self.icon_path):
            try:
                icon_img = ImageTk.PhotoImage(file=self.icon_path)
                self.iconphoto(False, icon_img)
                self._icon_ref = icon_img
            except Exception:
                pass

    def _build_header(self):
        """Формирование шапки калькулятора с логотипом компании."""
        header_frame = tk.Frame(self, bg="#FFFFFF", height=68, padx=20, pady=12)
        header_frame.pack(side="top", fill="x")

        tk.Frame(self, bg="#E5E7EB", height=1).pack(side="top", fill="x")

        if os.path.exists(self.logo_path):
            try:
                pil_logo = Image.open(self.logo_path)
                pil_logo = pil_logo.resize((44, 44), Image.Resampling.LANCZOS)
                logo_img = ImageTk.PhotoImage(pil_logo)
                logo_label = tk.Label(header_frame, image=logo_img, bg="#FFFFFF")
                logo_label.image = logo_img
                logo_label.pack(side="left", padx=(0, 14))
            except Exception:
                pass

        title_box = tk.Frame(header_frame, bg="#FFFFFF")
        title_box.pack(side="left")

        title_lbl = tk.Label(
            title_box,
            text="Калькулятор расхода материалов",
            font=("Arial", 14, "bold"),
            bg="#FFFFFF",
            fg="#111827"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            title_box,
            text="Нормативный расчет сырья с учетом коэффициентов и процента брака",
            font=("Arial", 9),
            bg="#FFFFFF",
            fg="#6B7280"
        )
        sub_lbl.pack(anchor="w")

    def _build_form(self):
        """Поля ввода параметров продукции и материалов."""
        container = tk.Frame(self, bg="#F4F6F9", padx=28, pady=16)
        container.pack(fill="x")

        # 1. Выбор типа продукции
        self._create_label(container, "Тип выпускаемой продукции *:")
        self.combo_product_type = ttk.Combobox(container, state="readonly", font=("Arial", 10))
        self.combo_product_type.pack(fill="x", pady=(0, 12))

        # 2. Выбор типа материала
        self._create_label(container, "Тип используемого материала (сырья) *:")
        self.combo_material_type = ttk.Combobox(container, state="readonly", font=("Arial", 10))
        self.combo_material_type.pack(fill="x", pady=(0, 12))

        # 3. Объем партии
        self._create_label(container, "Планируемое количество продукции (шт.) *:")
        self.entry_quantity = tk.Entry(container, font=("Arial", 10), relief="solid", bd=1)
        self.entry_quantity.pack(fill="x", pady=(0, 12))

        # 4. Физические параметры изделия
        params_row = tk.Frame(container, bg="#F4F6F9")
        params_row.pack(fill="x", pady=(0, 16))

        col1 = tk.Frame(params_row, bg="#F4F6F9")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._create_label(col1, "Параметр 1 (длина/размер, м) *:")
        self.entry_param1 = tk.Entry(col1, font=("Arial", 10), relief="solid", bd=1)
        self.entry_param1.pack(fill="x")

        col2 = tk.Frame(params_row, bg="#F4F6F9")
        col2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._create_label(col2, "Параметр 2 (ширина/высота, м) *:")
        self.entry_param2 = tk.Entry(col2, font=("Arial", 10), relief="solid", bd=1)
        self.entry_param2.pack(fill="x")

        # Кнопки управления
        btn_box = tk.Frame(container, bg="#F4F6F9")
        btn_box.pack(fill="x", pady=(4, 0))

        calc_btn = StyledButton(
            btn_box,
            text="Рассчитать потребность сырья",
            bg="#2A73C6",
            fg="#FFFFFF",
            hover_bg="#1E5BA3",
            font=("Arial", 10, "bold"),
            padx=18,
            pady=8,
            command=self.perform_calculation
        )
        calc_btn.pack(side="left", padx=(0, 10))

        clear_btn = StyledButton(
            btn_box,
            text="Очистить",
            bg="#E2E8F0",
            fg="#1E293B",
            hover_bg="#CBD5E1",
            font=("Arial", 10),
            padx=14,
            pady=8,
            command=self.reset_form
        )
        clear_btn.pack(side="left")

    def _create_label(self, parent, text):
        lbl = tk.Label(
            parent,
            text=text,
            font=("Arial", 9, "bold"),
            bg="#F4F6F9",
            fg="#374151"
        )
        lbl.pack(anchor="w", pady=(0, 4))
        return lbl

    def _build_result_panel(self):
        """Информационная панель вывода результатов расчета."""
        panel_box = tk.Frame(self, bg="#F4F6F9", padx=28, pady=8)
        panel_box.pack(fill="both", expand=True)

        card = tk.Frame(panel_box, bg="#FFFFFF", padx=20, pady=16, relief="solid", bd=1)
        card.configure(highlightbackground="#E2E8F0", highlightthickness=1)
        card.pack(fill="both", expand=True)

        result_header = tk.Label(
            card,
            text="Результат расчета расхода сырья:",
            font=("Arial", 11, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        )
        result_header.pack(anchor="w", pady=(0, 8))

        self.result_value_lbl = tk.Label(
            card,
            text="—",
            font=("Arial", 22, "bold"),
            bg="#FFFFFF",
            fg="#2A73C6"
        )
        self.result_value_lbl.pack(anchor="w", pady=(0, 8))

        self.details_lbl = tk.Label(
            card,
            text="Заполните параметры изделия и нажмите «Рассчитать потребность сырья».",
            font=("Arial", 9),
            bg="#FFFFFF",
            fg="#6B7280",
            justify="left"
        )
        self.details_lbl.pack(anchor="w")

    def _load_reference_data(self):
        """Загрузка доступных типов продукции и материалов из базы данных."""
        try:
            prod_types = self.db.get_product_types()
            mat_types = self.db.get_material_types()

            prod_names = []
            for item in prod_types:
                display_name = f"{item['type_name']} (коэф. {item['coefficient']})"
                prod_names.append(display_name)
                self.product_types_map[display_name] = item["id"]

            mat_names = []
            for item in mat_types:
                display_name = f"{item['type_name']} (брак {item['defect_rate']}%)"
                mat_names.append(display_name)
                self.material_types_map[display_name] = item["id"]

            self.combo_product_type["values"] = prod_names
            if prod_names:
                self.combo_product_type.current(0)

            self.combo_material_type["values"] = mat_names
            if mat_names:
                self.combo_material_type.current(0)

        except DatabaseConnectionError as err:
            AppDialogs.show_error(self, "Ошибка БД", f"Не удалось загрузить справочники: {err}")

    def perform_calculation(self):
        """
        Считывание параметров формы, валидация и вызов ядра алгоритма.
        При получении -1 форма не аварийно завершается, а показывает уведомление.
        """
        sel_prod = self.combo_product_type.get()
        sel_mat = self.combo_material_type.get()

        if not sel_prod or sel_prod not in self.product_types_map:
            AppDialogs.show_error(
                self,
                "Ошибка ввода",
                "Пожалуйста, выберите корректный тип продукции из списка."
            )
            return

        if not sel_mat or sel_mat not in self.material_types_map:
            AppDialogs.show_error(
                self,
                "Ошибка ввода",
                "Пожалуйста, выберите корректный тип материала из списка."
            )
            return

        product_type_id = self.product_types_map[sel_prod]
        material_type_id = self.material_types_map[sel_mat]

        # Валидация числовых значений
        raw_qty = self.entry_quantity.get().strip()
        raw_p1 = self.entry_param1.get().strip()
        raw_p2 = self.entry_param2.get().strip()

        try:
            quantity = int(raw_qty)
        except ValueError:
            self._handle_calculation_error(
                "Количество продукции должно быть положительным целым числом."
            )
            return

        try:
            param_1 = float(raw_p1.replace(",", "."))
            param_2 = float(raw_p2.replace(",", "."))
        except ValueError:
            self._handle_calculation_error(
                "Параметры изделия (размеры) должны быть вещественными положительными числами."
            )
            return

        # Вызов ядра алгоритма расчета
        result = calculate_material_requirement(
            product_type_id=product_type_id,
            material_type_id=material_type_id,
            quantity=quantity,
            param_1=param_1,
            param_2=param_2,
            db_manager=self.db
        )

        if result == -1:
            self._handle_calculation_error(
                "Алгоритм расчета вернул признак ошибки (-1).\n\n"
                "Проверьте правильность введенных данных:\n"
                "— Количество продукции должно быть строго больше 0;\n"
                "— Геометрические параметры изделия должны быть строго положительными (> 0);\n"
                "— Идентификаторы типов должны присутствовать в базе данных."
            )
            return

        # Успешный вывод результата расчета на форму
        formatted_result = f"{result:,} ед.".replace(",", " ")
        self.result_value_lbl.config(text=formatted_result, fg="#059669")

        info_text = (
            f"Тип изделия: {sel_prod}\n"
            f"Материал: {sel_mat}\n"
            f"Количество в заказе: {quantity:,} шт.\n"
            f"Параметры единицы: {param_1} x {param_2} м\n"
            f"Расчет выполнен успешно с учетом нормативного брака."
        )
        self.details_lbl.config(text=info_text, fg="#374151")

    def _handle_calculation_error(self, message: str):
        """Обработка ошибки расчета без падения интерфейса."""
        self.result_value_lbl.config(text="Ошибка данных", fg="#DC2626")
        self.details_lbl.config(
            text="Расчет не может быть выполнен из-за некорректных входных значений.",
            fg="#DC2626"
        )
        AppDialogs.show_error(self, "Некорректные параметры расчета", message)

    def reset_form(self):
        """Очистка полей формы."""
        self.entry_quantity.delete(0, tk.END)
        self.entry_param1.delete(0, tk.END)
        self.entry_param2.delete(0, tk.END)
        self.result_value_lbl.config(text="—", fg="#2A73C6")
        self.details_lbl.config(
            text="Заполните параметры изделия и нажмите «Рассчитать потребность сырья».",
            fg="#6B7280"
        )


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    win = MaterialCalculatorWindow(root)
    root.mainloop()
