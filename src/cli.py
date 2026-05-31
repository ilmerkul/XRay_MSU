"""CLI: расчёт порошковой дифрактограммы по YAML (OmegaConf)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

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

DEFAULT_CONFIG = "config/alpha-Fe.yaml"


def _cfg_float(cfg: Any, key: str) -> Optional[float]:
    """Извлекает вещественное значение из OmegaConf по ключу.

    Args:
        cfg: Конфигурация OmegaConf.
        key: Имя поля.

    Returns:
        Значение как ``float`` или ``None``, если ключ отсутствует или равен ``None``.
    """
    if key not in cfg or cfg[key] is None:
        return None
    return float(cfg[key])


def _lattice_params(cfg: Any) -> tuple[float, float, float, float, float, float]:
    """Возвращает a, b, c, α, β, γ (градусы) с учётом ``lattice_family`` из YAML.

    Args:
        cfg: Конфигурация кристалла из YAML.

    Returns:
        Шесть параметров решётки в градусах для углов.

    Raises:
        ValueError: Если для выбранной сингонии не хватает параметров.
    """
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


def discover_config_files() -> list[tuple[str, str]]:
    """Список доступных YAML-конфигов ``(имя_файла, абсолютный_путь)``."""
    by_name: dict[str, str] = {}
    search_dirs: list[Path] = []
    rp = resource_path("config")
    if rp:
        search_dirs.append(Path(rp))
    cwd_cfg = Path.cwd() / "config"
    if cwd_cfg.is_dir():
        search_dirs.append(cwd_cfg.resolve())

    for directory in search_dirs:
        if not directory.is_dir():
            continue
        for pattern in ("*.yaml", "*.yml"):
            for path in sorted(directory.glob(pattern)):
                if path.name not in by_name:
                    by_name[path.name] = str(path.resolve())
    return sorted(by_name.items(), key=lambda item: item[0].lower())


def _resolve_config_path(arg: str) -> str:
    """Находит путь к YAML-конфигу по аргументу CLI.

    Args:
        arg: Имя файла или относительный/абсолютный путь.

    Returns:
        Абсолютный путь к существующему файлу конфигурации.

    Raises:
        FileNotFoundError: Если конфиг не найден.
    """
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


def _require_questionary():
    try:
        import questionary
    except ImportError as exc:
        raise SystemExit(
            "Для интерактивного CLI установите зависимость:\n  uv sync --extra cli"
        ) from exc
    return questionary


def _prompt_cli_run(*, local_default: bool) -> tuple[str, bool]:
    """Интерактивный выбор конфига и режима атомных f через questionary."""
    questionary = _require_questionary()
    configs = discover_config_files()
    if not configs:
        raise SystemExit(
            "Не найдены YAML-конфиги в каталоге config/. "
            "Запустите из корня репозитория или укажите путь: "
            "python -m src --cli path/to/config.yaml"
        )

    default_name = Path(DEFAULT_CONFIG).name
    choices = [questionary.Choice(title=name, value=path) for name, path in configs]
    default_choice = next(
        (c for c in choices if c.title == default_name),
        choices[0],
    )

    cfg_path = questionary.select(
        "Выберите конфиг расчёта:",
        choices=choices,
        default=default_choice,
        use_indicator=True,
    ).ask()
    if cfg_path is None:
        raise SystemExit(0)

    use_local = questionary.confirm(
        "Использовать локальные f (Waas–Kirfel)?\n"
        "(Нет — xraylib; нужен uv sync --extra xraylib)",
        default=local_default,
    ).ask()
    if use_local is None:
        raise SystemExit(0)

    return cfg_path, use_local


def _execute_calculation(cfg_path: str, *, local: bool) -> None:
    """Загружает конфиг, считает дифрактограмму и сохраняет в ``runs/``."""
    cfg = OmegaConf.load(cfg_path)

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
        local=local,
    )

    out_dir = f"runs/{cfg.name}/"
    Plot(powder=pattern).plot_curve(path=out_dir)
    print(f"Готово: результаты в {out_dir}")


def run_cli(config_arg: str | None = None, *, local: bool = True) -> None:
    """Запускает расчёт: интерактивно (questionary) или по пути к YAML.

    Args:
        config_arg: Путь или имя конфига; если ``None`` — интерактивное меню.
        local: ``True`` — f из Waas–Kirfel; ``False`` — xraylib.
    """
    if config_arg is None:
        cfg_path, local = _prompt_cli_run(local_default=local)
    else:
        cfg_path = _resolve_config_path(config_arg)

    _execute_calculation(cfg_path, local=local)
