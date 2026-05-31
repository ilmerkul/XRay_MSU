"""Тесты ASCII-текстов Tk-интерфейса."""

from src.gui.ui_text import ascii_ui_text


def test_ascii_ui_text_greek_angles():
    assert ascii_ui_text("α (°):") == "alpha ( deg):"
    assert ascii_ui_text("2θ диапазон:") == "2theta диапазон:"


def test_ascii_ui_text_wavelength_ratio():
    assert ascii_ui_text("I(λ2)/I(λ1)") == "I(lambda2)/I(lambda1)"


def test_ascii_ui_text_angstrom():
    assert ascii_ui_text("a (Å):") == "a (A):"
