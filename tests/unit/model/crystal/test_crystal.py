import numpy as np
import pytest

from src.model.crystal.crystal import Crystal


class TestCrystalHKL:
    @pytest.mark.parametrize(
        ("hkl", "expected"),
        [
            ((1.1, 2.4, -0.6), (1, 2, -1)),
            ((0.0, 0.0, 0.0), (0, 0, 0)),
        ],
    )
    def test_hkl2tuple_rounds(self, hkl, expected):
        assert Crystal.hkl2tuple(hkl) == expected


class TestCrystalDSpacing:
    @pytest.fixture
    def cubic_a(self) -> float:
        return 5.64

    def test_111_spacing_cubic(self, nacl_crystal: Crystal, cubic_a: float):
        d = nacl_crystal.d_spacing((1, 1, 1))
        expected = cubic_a / np.sqrt(3)
        assert d == pytest.approx(expected, rel=1e-6)

    def test_invalid_reflection_returns_inf(self, nacl_crystal: Crystal):
        assert np.isinf(nacl_crystal.d_spacing((0, 0, 0)))


class TestCrystalMetrics:
    def test_volume_cubic_nacl(self, nacl_crystal: Crystal):
        a = nacl_crystal.a
        assert nacl_crystal.V == pytest.approx(a**3, rel=1e-6)

    def test_gstar_positive_definite(self, nacl_crystal: Crystal):
        eigvals = np.linalg.eigvalsh(nacl_crystal.Gstar)
        assert np.all(eigvals > 0)

    def test_d_spacing_bragg_consistency(self, nacl_crystal: Crystal):
        wavelength = 1.5418
        hkl = (1, 1, 1)
        d = nacl_crystal.d_spacing(hkl)
        theta = np.arcsin(wavelength / (2 * d))
        twotheta = np.degrees(2 * theta)
        assert 25 < twotheta < 35
