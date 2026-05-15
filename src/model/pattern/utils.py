import json

import numpy as np


def l_factor(twotheta_deg: float):
    th = np.radians(twotheta_deg / 2)
    return 1 / (np.sin(th) ** 2 * np.cos(th))


def p_factor(twotheta_deg: float, thetam_deg: float):
    th = np.radians(twotheta_deg / 2)
    thm = np.radians(thetam_deg)
    return (1 + np.cos(2 * th) ** 2 * np.cos(2 * thm) ** 2) / (1 + np.cos(2 * thm) ** 2)


def lp_factor(twotheta_deg: float, thetam_deg: float):
    return l_factor(twotheta_deg=twotheta_deg) * p_factor(
        twotheta_deg=twotheta_deg, thetam_deg=thetam_deg
    )


def gaussian(x, centre, fwhm):
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
    return (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(
        -0.5 * ((x - centre) / sigma) ** 2
    )


def lorentzian(x, centre, fwhm):
    gamma = fwhm / 2
    return (gamma / np.pi) / ((x - centre) ** 2 + gamma**2)


def pseudo_voigt(x, centre, fwhm, eta=0.5):
    return eta * lorentzian(x, centre, fwhm) + (1 - eta) * gaussian(x, centre, fwhm)


# Кальотти: FWHM_θ = sqrt(U tan²θ + V tanθ + W); очень узкие пики (~0.1× «широких»)
CAGLIOTI_U_DEFAULT = 0.00025
CAGLIOTI_V_DEFAULT = -0.000175
CAGLIOTI_W_DEFAULT = 0.0001


def caglioti_fwhm(theta, U, V, W):
    tant = np.tan(theta)
    return np.sqrt(U * tant**2 + V * tant + W)


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.complex128) or isinstance(obj, complex):
            return {"real": obj.real, "imag": obj.imag}
        return super().default(obj)


def array_weight(arr):
    def merge_count_inv(subarr):
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
