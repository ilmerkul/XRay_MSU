from omegaconf import OmegaConf

from src.model.atom.atom import Atom
from src.model.crystal.crystal import Crystal
from src.model.pattern.plot import Plot
from src.model.pattern.powder import PowderPattern

cfg = OmegaConf.load("config/test.yaml")

crystal = Crystal(
    cfg.a,
    cfg.b,
    cfg.c,
    cfg.alpha,
    cfg.beta,
    cfg.gamma,
    cfg.space_group,
    [Atom(*atom) for atom in cfg.atoms],
)


pattern = PowderPattern(
    cfg.name,
    crystal,
    cfg.wavelength,
    cfg.twotheta_range,
    U=cfg.U,
    V=cfg.V,
    W=cfg.W,
    scale=cfg.scale,
    profile=cfg.profile,
    eta=cfg.eta,
    intensity_units=cfg.intensity_units,
    normalize_intensity=cfg.normalize_intensity,
    intensity_max_value=cfg.intensity_max_value,
)

plot = Plot(pattern)

plot.plot_curve(path="images")
