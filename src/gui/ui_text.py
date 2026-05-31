"""Тексты Tk-интерфейса без символов, отсутствующих в типичных X11-шрифтах."""

from __future__ import annotations

# Порядок важен: более длинные шаблоны — раньше.
_ASCII_UI_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("2θ", "2theta"),
    ("θ", "theta"),
    ("α", "alpha"),
    ("β", "beta"),
    ("γ", "gamma"),
    ("η", "eta"),
    ("λ", "lambda"),
    ("Å", "A"),
    ("°", " deg"),
    ("≈", "~"),
    ("…", "..."),
    ("—", "-"),
)


def ascii_ui_text(text: str) -> str:
    """Заменяет Unicode-символы на ASCII для меток Tk/ttk."""
    if not text:
        return text
    for old, new in _ASCII_UI_REPLACEMENTS:
        text = text.replace(old, new)
    return text.replace(" deg deg", " deg")
