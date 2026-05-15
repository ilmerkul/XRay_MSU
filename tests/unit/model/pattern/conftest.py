import numpy as np
import pytest

from src.model.crystal.crystal import Crystal
from src.model.pattern.powder import PowderPattern


def make_powder_pattern(
    crystal: Crystal,
    twotheta_range: np.ndarray,
    *,
    profile: str = "bar",
    intensity_min: float = 1e-6,
    **kwargs,
) -> PowderPattern:
    defaults = dict(
        name="test",
        crystal=crystal,
        wavelength=1.5418,
        twotheta_range=twotheta_range,
        thetam_deg=0.0,
        profile=profile,
        normalize_intensity=True,
        intensity_max_value=100.0,
        save_ref=False,
        intensity_min=intensity_min,
    )
    defaults.update(kwargs)
    return PowderPattern(**defaults)


@pytest.fixture
def bar_pattern(
    nacl_crystal: Crystal,
    twotheta_range_nacl: np.ndarray,
) -> PowderPattern:
    return make_powder_pattern(nacl_crystal, twotheta_range_nacl, profile="bar")
