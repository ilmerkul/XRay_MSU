"""Вспомогательные функции для расчёта порошковой дифрактограммы."""

import json

import numpy as np


def l_factor(twotheta_deg: float):
    """Lorentz-фактор L для порошковой дифракции.

    Args:
        twotheta_deg: Угол 2θ в градусах.

    Returns:
        Значение L = 1 / (sin²θ · cos θ), где θ = 2θ/2.
    """
    th = np.radians(twotheta_deg / 2)
    return 1 / (np.sin(th) ** 2 * np.cos(th))


def p_factor(twotheta_deg: float, thetam_deg: float):
    """Поляризационный фактор P для монохроматического пучка.

    Args:
        twotheta_deg: Угол 2θ в градусах.
        thetam_deg: Угол θ_m поляризации первичного пучка (градусы).

    Returns:
        Значение поляризационного фактора P.
    """
    th = np.radians(twotheta_deg / 2)
    thm = np.radians(thetam_deg)
    return (1 + np.cos(2 * th) ** 2 * np.cos(2 * thm) ** 2) / (1 + np.cos(2 * thm) ** 2)


def lp_factor(twotheta_deg: float, thetam_deg: float):
    """Произведение L- и P-факторов.

    Args:
        twotheta_deg: Угол 2θ в градусах.
        thetam_deg: Угол θ_m поляризации (градусы).

    Returns:
        Значение L · P.
    """
    return l_factor(twotheta_deg=twotheta_deg) * p_factor(
        twotheta_deg=twotheta_deg, thetam_deg=thetam_deg
    )


def gaussian(x, centre, fwhm):
    """Нормированное гауссово распределение с заданной FWHM.

    Args:
        x: Массив абсцисс (например, 2θ).
        centre: Положение центра пика.
        fwhm: Полная ширина на полувысоте.

    Returns:
        Массив значений профиля (интеграл = 1).
    """
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
    return (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(
        -0.5 * ((x - centre) / sigma) ** 2
    )


def lorentzian(x, centre, fwhm):
    """Нормированное лоренцево распределение с заданной FWHM.

    Args:
        x: Массив абсцисс.
        centre: Положение центра пика.
        fwhm: Полная ширина на полувысоте.

    Returns:
        Массив значений профиля.
    """
    gamma = fwhm / 2
    return (gamma / np.pi) / ((x - centre) ** 2 + gamma**2)


def pseudo_voigt(x, centre, fwhm, eta=0.5):
    """Псевдо-Voigt: линейная смесь Lorentz и Gaussian.

    Args:
        x: Массив абсцисс.
        centre: Положение центра пика.
        fwhm: Полная ширина на полувысоте.
        eta: Доля лоренцевой компоненты (0 — чистый Gaussian).

    Returns:
        Массив значений профиля.
    """
    return eta * lorentzian(x, centre, fwhm) + (1 - eta) * gaussian(x, centre, fwhm)


_PROFILE_ALIASES = {"stick": "bar", "штрих": "bar"}


def normalize_profile(profile: str) -> str:
    """Приводит имя профиля к каноническому виду.

    Args:
        profile: Имя профиля (``bar``, ``gaussian``, ``stick``, ``штрих`` и т.д.).

    Returns:
        Каноническое имя: ``bar``, ``gaussian``, ``lorentzian`` или ``pseudo_voigt``.
    """
    key = profile.strip().lower()
    return _PROFILE_ALIASES.get(key, key)


# Кальотти: FWHM_θ = sqrt(U tan²θ + V tanθ + W); очень узкие пики (~0.1× «широких»)
CAGLIOTI_U_DEFAULT = 0.00025
CAGLIOTI_V_DEFAULT = -0.000175
CAGLIOTI_W_DEFAULT = 0.0001


def caglioti_fwhm(theta, U, V, W):
    """Ширина пика по формуле Кальотти (FWHM в радианах θ).

    Args:
        theta: Угол θ (радианы).
        U: Параметр U профиля Кальотти.
        V: Параметр V профиля Кальотти.
        W: Параметр W профиля Кальотти.

    Returns:
        FWHM в радианах: sqrt(U tan²θ + V tan θ + W).
    """
    tant = np.tan(theta)
    return np.sqrt(U * tant**2 + V * tant + W)


class NumpyEncoder(json.JSONEncoder):
    """JSON-кодировщик с поддержкой ``numpy.complex128`` и ``complex``."""

    def default(self, obj):
        """Сериализует комплексные числа как ``{real, imag}``.

        Args:
            obj: Объект для сериализации.

        Returns:
            Словарь с полями ``real`` и ``imag`` для комплексных типов.

        Raises:
            TypeError: Для типов, не поддерживаемых базовым encoder.
        """
        if isinstance(obj, np.complex128) or isinstance(obj, complex):
            return {"real": obj.real, "imag": obj.imag}
        return super().default(obj)


def array_weight(arr):
    """Число инверсий в массиве (для лексикографического сравнения hkl).

    Args:
        arr: Последовательность чисел (например, индексы h, k, l).

    Returns:
        Число пар (i, j) с i < j и arr[i] > arr[j].
    """

    def merge_count_inv(subarr):
        """Рекурсивно считает инверсии при сортировке слиянием.

        Args:
            subarr: Подмассив.

        Returns:
            Кортеж (отсортированный подмассив, число инверсий).
        """
        if len(subarr) <= 1:
            return subarr, 0
        mid = len(subarr) // 2
        left, inv_left = merge_count_inv(subarr[:mid])
        right, inv_right = merge_count_inv(subarr[mid:])
        merged = []
        i = j = 0
        inv = inv_left + inv_right
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                inv += len(left) - i
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, inv

    _, inversions = merge_count_inv(arr)
    return inversions
