from omegaconf import OmegaConf

from src.model.atom.atom import Atom, AtomicScatteringFactor
from src.model.crystal.crystal import Crystal
from src.model.pattern.plot import Plot
from src.model.pattern.powder import PowderPattern

cfg = OmegaConf.load("config/test1.yaml")

asf = AtomicScatteringFactor("data/f0_WaasKirf.dat")

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
)

plot = Plot(powder=pattern)

plot.plot_curve(path=f"runs/{cfg.name}/")
