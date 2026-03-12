import json

import numpy as np


def lp_factor(twotheta):
    th = np.radians(twotheta / 2)
    return (1 + np.cos(2 * th) ** 2) / (np.sin(th) ** 2 * np.cos(th))


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
