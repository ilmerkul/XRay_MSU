import json

import numpy as np
import pytest

from src.model.pattern.utils import (
    CAGLIOTI_U_DEFAULT,
    CAGLIOTI_V_DEFAULT,
    CAGLIOTI_W_DEFAULT,
    NumpyEncoder,
    array_weight,
    caglioti_fwhm,
    gaussian,
    l_factor,
    lorentzian,
    lp_factor,
    normalize_profile,
    p_factor,
    pseudo_voigt,
)


class TestNormalizeProfile:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("bar", "bar"),
            ("stick", "bar"),
            ("штрих", "bar"),
            ("  Gaussian  ", "gaussian"),
        ],
    )
    def test_aliases_and_strip(self, raw: str, expected: str):
        assert normalize_profile(raw) == expected


class TestCaglioti:
    @pytest.fixture
    def default_coeffs(self):
        return CAGLIOTI_U_DEFAULT, CAGLIOTI_V_DEFAULT, CAGLIOTI_W_DEFAULT

    @pytest.mark.parametrize("twotheta_deg", [20.0, 50.0, 80.0, 120.0])
    def test_default_width_positive(self, twotheta_deg: float, default_coeffs):
        u, v, w = default_coeffs
        theta = np.radians(twotheta_deg / 2)
        assert caglioti_fwhm(theta, u, v, w) > 0


class TestLineProfiles:
    @pytest.fixture
    def grid(self):
        return np.linspace(-5, 5, 2001)

    def test_gaussian_integral_is_one(self, grid, integrate_1d):
        integral = integrate_1d(gaussian(grid, 0.0, 1.0), grid)
        assert integral == pytest.approx(1.0, rel=1e-3)

    def test_lorentzian_peak_at_centre(self):
        y_centre = lorentzian(np.array([2.0]), 2.0, 0.5)[0]
        y_offset = lorentzian(np.array([2.5]), 2.0, 0.5)[0]
        assert y_centre > y_offset

    def test_pseudo_voigt_between_gaussian_and_lorentzian(self):
        x = np.array([1.0])
        g = gaussian(x, 1.0, 0.4)[0]
        lor = lorentzian(x, 1.0, 0.4)[0]
        pv = pseudo_voigt(x, 1.0, 0.4, eta=0.5)[0]
        assert min(g, lor) <= pv <= max(g, lor)


class TestNumpyEncoder:
    def test_complex_roundtrip(self):
        payload = {"F": 1 + 2j}
        text = json.dumps(payload, cls=NumpyEncoder)
        loaded = json.loads(text)
        assert loaded["F"]["real"] == 1.0
        assert loaded["F"]["imag"] == 2.0

    def test_small_complex_roundtrip(self):
        payload = {"F": 1e-12 + 1e-12j}
        loaded = json.loads(json.dumps(payload, cls=NumpyEncoder))
        assert loaded["F"]["real"] == pytest.approx(0.0, abs=1e-9)
        assert loaded["F"]["imag"] == pytest.approx(0.0, abs=1e-9)


class TestLorentzPolarization:
    def test_l_factor_decreases_with_twotheta_at_moderate_angles(self):
        low_tt = l_factor(20.0)
        high_tt = l_factor(80.0)
        assert low_tt > high_tt > 0

    def test_p_factor_positive_and_bounded(self):
        p = p_factor(40.0, thetam_deg=0.0)
        assert 0 < p <= 1.0

    def test_lp_factor_is_product(self):
        tt, tm = 35.0, 10.0
        assert lp_factor(tt, tm) == pytest.approx(l_factor(tt) * p_factor(tt, tm))


class TestArrayWeight:
    @pytest.mark.parametrize(
        ("indices", "expected_inversions"),
        [
            ([1, 2, 3], 0),
            ([3, 2, 1], 3),
            ([1, 3, 2], 1),
        ],
    )
    def test_inversion_count(self, indices, expected_inversions):
        assert array_weight(indices) == expected_inversions


class TestCagliotiScaling:
    def test_wider_coefficients_give_larger_fwhm(self):
        theta = np.radians(25.0)
        narrow = caglioti_fwhm(theta, 0.0001, -0.00005, 0.00005)
        wide = caglioti_fwhm(theta, 0.001, -0.0005, 0.0005)
        assert wide > narrow


class TestPseudoVoigtLimits:
    @pytest.fixture
    def x_grid(self):
        return np.linspace(9.5, 10.5, 101)

    def test_eta_zero_matches_gaussian(self, x_grid):
        centre, fwhm = 10.0, 0.2
        assert np.allclose(
            pseudo_voigt(x_grid, centre, fwhm, eta=0.0),
            gaussian(x_grid, centre, fwhm),
        )

    def test_eta_one_matches_lorentzian(self, x_grid):
        centre, fwhm = 10.0, 0.2
        assert np.allclose(
            pseudo_voigt(x_grid, centre, fwhm, eta=1.0),
            lorentzian(x_grid, centre, fwhm),
        )
