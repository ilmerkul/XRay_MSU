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
