"""Построение и сохранение графиков порошковой дифрактограммы."""

from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

from src.model.crystal.crystal import Crystal
from src.model.pattern.powder import PowderPattern


class Plot:
    """Экспорт дифрактограммы и связанных данных на диск."""

    def __init__(self, powder: PowderPattern):
        """Привязывает объект расчёта к построителю графиков.

        Args:
            powder: Рассчитанная порошковая дифрактограмма.
        """
        self.powder = powder

    @staticmethod
    def save_powder_png(
        filepath: Union[str, Path],
        twotheta,
        y,
        hkl_labels,
        title: str,
        *,
        ylabel: str = "Intensity",
        xlim: tuple[float, float] | None = None,
        line_color: str = "#0b7285",
        facecolor: str = "#fafbfc",
    ) -> None:
        """Сохраняет кривую дифрактограммы в PNG.

        Args:
            filepath: Путь к выходному файлу.
            twotheta: Массив углов 2θ (градусы).
            y: Массив интенсивностей.
            hkl_labels: Список ``(hkl, x, y_peak)`` для подписей пиков.
            title: Заголовок графика.
            ylabel: Подпись оси ординат.
            xlim: Пределы оси 2θ; по умолчанию от ``twotheta[0]`` до ``twotheta[-1]``.
            line_color: Цвет кривой.
            facecolor: Фон рисунка.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        fig = plt.figure(figsize=(10, 4), facecolor=facecolor)
        try:
            ax = fig.add_subplot(111)
            ax.set_facecolor(facecolor)
            ax.plot(twotheta, y, label=title, color=line_color, linewidth=1.2)
            ax.set_xlabel("2θ (deg)")
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            x0 = float(twotheta[0]) if xlim is None else float(xlim[0])
            x1 = float(twotheta[-1]) if xlim is None else float(xlim[1])
            y_arr = np.asarray(y, dtype=float)
            y_top = float(np.max(y_arr)) if y_arr.size else 1.0
            ax.xaxis.set_major_locator(MultipleLocator(10))
            ax.xaxis.set_minor_locator(MultipleLocator(1))
            ax.tick_params(axis="x", which="major", length=6)
            ax.tick_params(axis="x", which="minor", length=3)
            for _hkl, x_peak, y_peak in hkl_labels:
                y_top = max(y_top, float(y_peak))
                ax.text(
                    x_peak,
                    y_peak,
                    f"{x_peak:.2f}°",
                    fontsize=6,
                    ha="center",
                    va="bottom",
                )
            ax.legend()
            ax.grid(True, alpha=0.35)
            ax.set_autoscale_on(False)
            ax.set_xlim(x0, x1)
            ax.set_ylim(0.0, y_top * 1.08 if y_top > 0 else 1.0)
            ax.margins(0)
            fig.savefig(filepath, facecolor=facecolor, bbox_inches="tight")
        finally:
            plt.close(fig)

    def plot_curve(self, path: Union[str, Path] = "."):
        """Сохраняет таблицу отражений, метрики G/G* и PNG дифрактограммы и ячейки.

        Args:
            path: Каталог для выходных файлов.
        """
        if isinstance(path, str):
            path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.powder.save_outputs(path)
        hkl_plot = [(hkl, x, y) for hkl, x, y in self.powder.hkl_labels]
        self.save_powder_png(
            path / f"{self.powder.name}_powder.png",
            self.powder.twotheta,
            self.powder.ycalc,
            hkl_plot,
            self.powder.name,
        )
        self.powder.crystal.save_image(filename=path / f"{self.powder.name}.png")

    def plot_point(self):
        """Демонстрация подгонки параметров (синтетические «экспериментальные» данные)."""
        import scipy.optimize

        y_exp_synth = self.powder.ycalc + np.random.normal(
            0, 0.1 * self.powder.ycalc.max(), size=len(self.powder.twotheta)
        )
        twotheta_exp = self.powder.twotheta

        params0 = [0.9, 0.02, -0.01, 0.008, 0.4, 5.4]

        result = scipy.optimize.leastsq(
            self.residual,
            params0,
            args=(
                twotheta_exp,
                y_exp_synth,
                self.powder.crystal,
                self.powder.wavelength,
            ),
        )
        params_refined = result[0]

        y_calc_refined = PowderPattern(
            self.powder.crystal,
            self.powder.wavelength,
            (20, 100, 0.02),
            U=params_refined[1],
            V=params_refined[2],
            W=params_refined[3],
            scale=params_refined[0],
            eta=params_refined[4],
        ).ycalc

        print("Refined parameters:")
        print(f"Scale = {params_refined[0]:.4f}")
        print(f"U = {params_refined[1]:.4f}")
        print(f"V = {params_refined[2]:.4f}")
        print(f"W = {params_refined[3]:.4f}")
        print(f"eta = {params_refined[4]:.4f}")
        print(f"a = {params_refined[5]:.4f}")

        plt.figure(figsize=(10, 4))
        plt.plot(twotheta_exp, y_exp_synth, "k.", markersize=1, label="Exp (synthetic)")
        plt.plot(
            twotheta_exp,
            np.interp(twotheta_exp, self.powder.twotheta, y_calc_refined),
            "r-",
            label="Refined",
        )
        plt.xlabel("2θ (deg)")
        plt.ylabel("Intensity")
        plt.title("Rietveld refinement test with spglib")
        plt.legend()
        plt.grid(True)
        plt.savefig("2.png")

    def residual(
        params,
        twotheta_exp,
        y_exp,
        crystal_template: Crystal,
        wavelength,
        profile="pvoigt",
    ):
        """Невязка для leastsq: разность эксперимента и расчётной кривой.

        Args:
            params: ``[scale, U, V, W, eta, a]`` — подгоняемые параметры.
            twotheta_exp: Углы 2θ эксперимента.
            y_exp: Экспериментальные интенсивности.
            crystal_template: Шаблон кристалла (копируется и масштабируется).
            wavelength: Длина волны (Å).
            profile: Имя профиля пика.

        Returns:
            Массив невязок ``y_exp - y_calc``.
        """
        scale, U, V, W, eta, a = params
        crystal_copy = crystal_template.copy()
        crystal_copy.a = a
        crystal_copy.b = a
        crystal_copy.c = a
        crystal_copy._compute_metrics()
        crystal_copy._lattice_matrix = Crystal.lattice_to_matrix(a, a, a, 90, 90, 90)

        crystal_copy.rotations, crystal_copy.translations = (
            crystal_copy._get_symmetry_operations()
        )
        crystal_copy.full_atoms = crystal_copy._generate_full_atoms()

        pattern = PowderPattern(
            crystal_copy,
            wavelength,
            (twotheta_exp[0], twotheta_exp[-1], 0.02),
            U=U,
            V=V,
            W=W,
            scale=scale,
            profile=profile,
            eta=eta,
        )
        y_calc_interp = np.interp(twotheta_exp, pattern.twotheta, pattern.ycalc)
        return y_exp - y_calc_interp
