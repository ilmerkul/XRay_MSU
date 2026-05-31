"""Вспомогательные функции ввода для GUI."""

import tkinter as tk
from tkinter import messagebox


def parse_float_locale(s: str) -> float:
    """Парсит число из текстового поля с учётом локали Windows.

    Args:
        s: Строка из виджета ввода.

    Returns:
        Число с плавающей точкой (запятая заменяется на точку).
    """
    t = str(s).strip().replace(",", ".").replace(" ", "")
    return float(t)


def safe_double_get(var, field_label: str):
    """Безопасно читает значение ``tk.DoubleVar``.

    Args:
        var: Переменная ``DoubleVar``.
        field_label: Подпись поля для сообщения об ошибке.

    Returns:
        Значение переменной или ``None`` при ``TclError`` (неверный формат).
    """
    try:
        return var.get()
    except tk.TclError:
        messagebox.showerror(
            "Input Error",
            f"Invalid number in {field_label}. Use a dot as decimal separator (e.g. 1.5).",
        )
        return None
