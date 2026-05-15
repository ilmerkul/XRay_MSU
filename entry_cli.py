#!/usr/bin/env python3
"""CLI: расчёт порошковой дифрактограммы по YAML (OmegaConf). PyInstaller: entry_cli.py."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

if getattr(sys, "frozen", False):
    sys.path.insert(0, sys._MEIPASS)
    os.chdir(Path(sys.executable).parent)
else:
    _ROOT = Path(__file__).resolve().parent
    sys.path.insert(0, str(_ROOT))
    os.chdir(_ROOT)

from omegaconf import OmegaConf

from src.model.atom.atom import Atom, AtomicScatteringFactor
from src.model.crystal.crystal import Crystal
from src.model.crystal.utils import expand_atoms_bravais_centering
from src.model.pattern.plot import Plot
from src.model.pattern.powder import PowderPattern
from src.model.pattern.utils import (
    CAGLIOTI_U_DEFAULT,
    CAGLIOTI_V_DEFAULT,
    CAGLIOTI_W_DEFAULT,
    normalize_profile,
)
from src.runtime_layout import asf_data_path, resource_path


def _cfg_float(cfg: Any, key: str) -> Optional[float]:
    if key not in cfg or cfg[key] is None:
        return None
    return float(cfg[key])


def _lattice_params(cfg: Any) -> tuple[float, float, float, float, float, float]:
    """a,b,c,α,β,γ (градусы) с учётом lattice_family из YAML."""
    fam = str(cfg.get("lattice_family") or cfg.get("crystal_system") or "manual")
    fam = fam.strip().lower()

    def g(key: str) -> Optional[float]:
        return _cfg_float(cfg, key)

    if fam == "cubic":
        side = g("a") or g("b") or g("c")
        if side is None:
            raise ValueError("cubic: задайте a (или b/c)")
        return side, side, side, 90.0, 90.0, 90.0
    if fam == "tetragonal":
        aa = g("a") or g("b")
        cc = g("c")
        if aa is None or cc is None:
            raise ValueError("tetragonal: задайте a и c")
        return aa, aa, cc, 90.0, 90.0, 90.0
    if fam == "orthorhombic":
        a, b, c = g("a"), g("b"), g("c")
        if None in (a, b, c):
            raise ValueError("orthorhombic: задайте a, b, c")
        return a, b, c, 90.0, 90.0, 90.0
    if fam == "hexagonal":
        aa = g("a") or g("b")
        cc = g("c")
        if aa is None or cc is None:
            raise ValueError("hexagonal: задайте a и c")
        return aa, aa, cc, 90.0, 90.0, 120.0
    if fam == "rhombohedral":
        side = g("a") or g("b") or g("c")
        ang = g("alpha") or g("beta") or g("gamma")
        if side is None or ang is None:
            raise ValueError("rhombohedral: задайте a и alpha")
        return side, side, side, ang, ang, ang
    if fam == "monoclinic":
        a, b, c = g("a"), g("b"), g("c")
        if None in (a, b, c):
            raise ValueError("monoclinic: задайте a, b, c")
        beta = g("beta")
        if beta is None:
            raise ValueError("monoclinic: задайте beta")
        return a, b, c, 90.0, beta, 90.0

    a = g("a")
    b = g("b") if g("b") is not None else a
    c = g("c") if g("c") is not None else a
    alpha = g("alpha") if g("alpha") is not None else 90.0
    beta = g("beta") if g("beta") is not None else 90.0
    gamma = g("gamma") if g("gamma") is not None else 90.0
    if a is None:
        raise ValueError("Задайте параметры решётки (a, …) или lattice_family")
    return a, b, c, alpha, beta, gamma


def _resolve_config_path(arg: str) -> str:
    name = Path(arg).name
    rp = resource_path("config", name)
    if rp:
        return rp
    p = Path(arg)
    if p.is_file():
        return str(p.resolve())
    root_p = Path.cwd() / arg
    if root_p.is_file():
        return str(root_p.resolve())
    raise FileNotFoundError(f"Конфиг не найден: {arg}")


def main() -> None:
    default_cfg = "config/alpha-Fe.yaml"
    cfg_arg = sys.argv[1] if len(sys.argv) > 1 else default_cfg
    cfg = OmegaConf.load(_resolve_config_path(cfg_arg))

    asf = AtomicScatteringFactor(asf_data_path())
    a, b, c, alpha, beta, gamma = _lattice_params(cfg)

    atoms = [Atom(*atom) for atom in cfg.atoms]
    sg = cfg.get("space_group")
    spacegroup_number = None if sg is None else int(sg)

    bravais = str(cfg.get("bravais_centering") or cfg.get("cubic_bravais") or "none")
    bravais = bravais.strip().lower()
    if bravais == "p":
        bravais = "none"
    if spacegroup_number is None and bravais not in ("", "none"):
        atoms = expand_atoms_bravais_centering(atoms, bravais.upper())

    crystal = Crystal(
        a=a,
        b=b,
        c=c,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        asf=asf,
        spacegroup_number=spacegroup_number,
        atoms=atoms,
    )

    pattern = PowderPattern(
        name=cfg.name,
        crystal=crystal,
        wavelength=float(cfg.wavelength),
        twotheta_range=cfg.twotheta_range,
        thetam_deg=float(cfg.get("thetam_deg", 0.0)),
        U=float(cfg.get("U", CAGLIOTI_U_DEFAULT)),
        V=float(cfg.get("V", CAGLIOTI_V_DEFAULT)),
        W=float(cfg.get("W", CAGLIOTI_W_DEFAULT)),
        scale=float(cfg.get("scale", 1.0)),
        profile=normalize_profile(str(cfg.get("profile", "gaussian"))),
        eta=float(cfg.get("eta", 0.5)),
        intensity_units=str(cfg.get("intensity_units", "arbitrary")),
        normalize_intensity=bool(cfg.get("normalize_intensity", True)),
        intensity_max_value=float(cfg.get("intensity_max_value", 100.0)),
        intensity_min=float(cfg.get("intensity_min", 1e-6)),
        multiplicity_mode=str(cfg.get("multiplicity_mode", "metric")),
        multiplicity_metric_rtol=float(cfg.get("multiplicity_metric_rtol", 1e-7)),
        multiplicity_metric_atol=float(cfg.get("multiplicity_metric_atol", 1e-12)),
    )

    Plot(powder=pattern).plot_curve(path=f"runs/{cfg.name}/")


if __name__ == "__main__":
    main()
