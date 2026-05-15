from pathlib import Path

import numpy as np
import pytest

from src.model.atom.atom import Atom, AtomicScatteringFactor
from src.model.crystal.crystal import Crystal


@pytest.fixture
def integrate_1d():
    if hasattr(np, "trapezoid"):
        return np.trapezoid
    return np.trapz


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="session")
def asf_path(repo_root: Path) -> Path:
    path = repo_root / "data" / "f0_WaasKirf.dat"
    if not path.is_file():
        pytest.skip("ASF data file missing")
    head = path.read_text(encoding="utf-8", errors="replace")[:80]
    if head.startswith("version https://git-lfs.github.com/spec/v1"):
        pytest.skip("data/f0_WaasKirf.dat is a Git LFS pointer; run: git lfs pull")
    return path


@pytest.fixture(scope="session")
def asf(asf_path: Path) -> AtomicScatteringFactor:
    return AtomicScatteringFactor(str(asf_path))


@pytest.fixture(scope="module")
def nacl_crystal(asf: AtomicScatteringFactor) -> Crystal:
    pytest.importorskip("spglib")
    return Crystal(
        a=5.64,
        b=5.64,
        c=5.64,
        alpha=90.0,
        beta=90.0,
        gamma=90.0,
        asf=asf,
        spacegroup_number=None,
        atoms=[
            Atom("Na", 0.0, 0.0, 0.0, 1.0, 1.6),
            Atom("Cl", 0.5, 0.5, 0.5, 1.0, 1.35),
        ],
    )


@pytest.fixture
def twotheta_range_nacl() -> np.ndarray:
    return np.array([10.0, 80.0, 0.05])


@pytest.fixture
def twotheta_range_narrow() -> np.ndarray:
    return np.array([30.0, 45.0, 0.02])


@pytest.fixture
def twotheta_range_peak() -> np.ndarray:
    """Узкий диапазон вокруг сильного пика NaCl (111)."""
    return np.array([31.0, 34.0, 0.01])


@pytest.fixture
def twotheta_grid_empty() -> np.ndarray:
    """Диапазон без брэгговских отражений для NaCl (Cu Kα)."""
    return np.array([5.0, 8.0, 0.01])
