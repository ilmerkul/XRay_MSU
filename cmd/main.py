import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    sys.path.insert(0, sys._MEIPASS)
    os.chdir(Path(sys.executable).parent)
else:
    _ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_ROOT))
    os.chdir(_ROOT)

from omegaconf import OmegaConf

from src.model.atom.atom import Atom, AtomicScatteringFactor
from src.model.crystal.crystal import Crystal
from src.model.pattern.plot import Plot
from src.model.pattern.powder import PowderPattern
from src.runtime_layout import resource_path

_cfg = resource_path("config", "alpha-Fe_structure.yaml")
if not _cfg:
    _cfg = str(Path.cwd() / "config" / "alpha-Fe_structure.yaml")
cfg = OmegaConf.load(_cfg)

_asf = resource_path("data", "f0_WaasKirf.dat")
if not _asf:
    _asf = "data/f0_WaasKirf.dat"
asf = AtomicScatteringFactor(_asf)

crystal = Crystal(
    a=cfg.a,
    b=cfg.b,
    c=cfg.c,
    alpha=cfg.alpha,
    beta=cfg.beta,
    gamma=cfg.gamma,
    asf=asf,
    spacegroup_number=cfg.space_group,
    atoms=[Atom(*atom) for atom in cfg.atoms],
)

pattern = PowderPattern(
    name=cfg.name,
    crystal=crystal,
    wavelength=cfg.wavelength,
    twotheta_range=cfg.twotheta_range,
    thetam_deg=cfg.thetam_deg,
    U=cfg.U,
    V=cfg.V,
    W=cfg.W,
    scale=cfg.scale,
    profile=cfg.profile,
    eta=cfg.eta,
    intensity_units=cfg.intensity_units,
    normalize_intensity=cfg.normalize_intensity,
    intensity_max_value=cfg.intensity_max_value,
    intensity_min=cfg.intensity_min,
    multiplicity_mode=cfg.get("multiplicity_mode", "symmetry"),
    multiplicity_metric_rtol=float(cfg.get("multiplicity_metric_rtol", 1e-7)),
    multiplicity_metric_atol=float(cfg.get("multiplicity_metric_atol", 1e-12)),
)

plot = Plot(powder=pattern)

plot.plot_curve(path=f"runs/{cfg.name}/")
