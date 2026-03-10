from omegaconf import OmegaConf

from src.model.atom.atom import Atom
from src.model.crystal.crystal import Crystal
from src.model.pattern.plot import Plot
from src.model.pattern.powder import PowderPattern

#cfg = OmegaConf.load("config/Si.yaml")
cfg = OmegaConf.load("config/NaCl.yaml")

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
    (20, 100, 0.02),
    U=0.01,
    V=-0.005,
    W=0.005,
    scale=1.0,
    profile="stick",
    eta=0.5,
)

plot = Plot(pattern)

plot.plot_curve()
