import numpy as np
import pytest

from src.model.crystal.crystal import Crystal
from src.model.pattern.powder import PowderPattern

from .conftest import make_powder_pattern


class TestPowderPattern:
    def test_has_reflections(self, bar_pattern: PowderPattern):
        assert len(bar_pattern.reflections) > 0

    def test_continuous_curve_non_empty(self, bar_pattern: PowderPattern):
        x, y = bar_pattern.get_pattern_data()
        assert len(x) == len(y)
        assert float(np.max(y)) > 0

    def test_profile_stick_alias_resolves_to_bar(self, nacl_crystal: Crystal):
        pattern = make_powder_pattern(
            nacl_crystal,
            np.array([20.0, 60.0, 0.1]),
            name="NaCl-stick",
            profile="stick",
        )
        assert pattern.profile == "bar"

    def test_twotheta_grid_matches_range(self, bar_pattern: PowderPattern):
        x, _ = bar_pattern.get_pattern_data()
        assert x[0] == pytest.approx(10.0)
        assert x[-1] < 80.0
        assert len(x) > 100


class TestPowderPatternValidation:
    def test_invalid_multiplicity_mode_raises(self, nacl_crystal: Crystal):
        with pytest.raises(ValueError, match="multiplicity_mode"):
            make_powder_pattern(
                nacl_crystal,
                np.array([20.0, 60.0, 0.1]),
                multiplicity_mode="invalid",
            )


class TestPowderProfiles:
    @pytest.fixture
    def peak_patterns(self, nacl_crystal: Crystal, twotheta_range_peak: np.ndarray):
        return {
            "bar": make_powder_pattern(
                nacl_crystal, twotheta_range_peak, profile="bar"
            ),
            "gaussian": make_powder_pattern(
                nacl_crystal, twotheta_range_peak, profile="gaussian"
            ),
        }

    def test_gaussian_has_more_nonzero_bins_than_bar(
        self, peak_patterns: dict[str, PowderPattern]
    ):
        _, y_bar = peak_patterns["bar"].get_pattern_data()
        _, y_gau = peak_patterns["gaussian"].get_pattern_data()
        nz_bar = int(np.count_nonzero(y_bar > 1e-6))
        nz_gau = int(np.count_nonzero(y_gau > 1e-6))
        assert nz_gau > nz_bar

    def test_normalized_gaussian_max_equals_intensity_max(
        self, peak_patterns: dict[str, PowderPattern]
    ):
        _, y_gau = peak_patterns["gaussian"].get_pattern_data()
        assert float(np.max(y_gau)) == pytest.approx(100.0, rel=1e-3)


class TestPowderIntensity:
    def test_high_intensity_min_filters_reflections(self, nacl_crystal: Crystal):
        loose = make_powder_pattern(
            nacl_crystal,
            np.array([10.0, 80.0, 0.1]),
            intensity_min=1e-6,
        )
        strict = make_powder_pattern(
            nacl_crystal,
            np.array([10.0, 80.0, 0.1]),
            intensity_min=1e12,
        )
        assert len(strict.reflections) < len(loose.reflections)

    def test_background_polynomial_raises_baseline(
        self, nacl_crystal: Crystal, twotheta_range_narrow: np.ndarray
    ):
        # np.polyval([a, b, c], x) = a·x² + b·x + c → константа в последнем коэффициенте
        zero_bg = make_powder_pattern(
            nacl_crystal,
            twotheta_range_narrow,
            profile="bar",
            bg_poly=[0.0, 0.0, 0.0],
        )
        raised = make_powder_pattern(
            nacl_crystal,
            twotheta_range_narrow,
            profile="bar",
            bg_poly=[0.0, 0.0, 10.0],
        )
        assert float(np.min(raised.ycalc)) >= float(np.min(zero_bg.ycalc)) + 9.0
        x = zero_bg.twotheta
        assert np.allclose(
            np.polyval(raised.bg_poly, x) - np.polyval(zero_bg.bg_poly, x),
            10.0,
        )


class TestPowderSetParams:
    def test_set_params_updates_attribute(self, bar_pattern: PowderPattern):
        bar_pattern.set_params(scale=3.5)
        assert bar_pattern.scale == 3.5

    def test_set_params_unknown_attribute_raises(self, bar_pattern: PowderPattern):
        with pytest.raises(AttributeError):
            bar_pattern.set_params(not_a_field=1)

    def test_generate_pattern_recomputes_curve(self, nacl_crystal: Crystal):
        pattern = make_powder_pattern(
            nacl_crystal,
            np.array([30.0, 50.0, 0.05]),
            profile="bar",
            normalize_intensity=False,
        )
        y0_max = float(np.max(pattern.get_pattern_data()[1]))
        pattern.set_params(scale=2.0)
        pattern.generate_pattern()
        y1_max = float(np.max(pattern.get_pattern_data()[1]))
        assert y1_max > y0_max * 1.9
