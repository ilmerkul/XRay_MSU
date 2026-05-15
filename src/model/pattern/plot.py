import os
from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

from src.model.crystal.crystal import Crystal
from src.model.pattern.powder import PowderPattern


class Plot:
    def __init__(self, powder: PowderPattern):
        self.powder = powder

    def plot_curve(self, path: Union[str, Path] = "."):
        os.makedirs(path, exist_ok=True)

        if isinstance(path, str):
            path = Path(path)
        plt.figure(figsize=(10, 4))
        plt.plot(self.powder.twotheta, self.powder.ycalc, label=self.powder.name)
        plt.xlabel("2θ (deg)")
        plt.ylabel("Intensity")
        plt.title(self.powder.name)
        ax = plt.gca()
        ax.xaxis.set_major_locator(MultipleLocator(10))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.tick_params(axis="x", which="major", length=6)
        ax.tick_params(axis="x", which="minor", length=3)
        for hkl, x, y in self.powder.hkl_labels:
            plt.text(x, y, "".join(map(str, hkl)), fontsize=6)
        plt.legend()
        plt.grid(True)
        plt.savefig(path / f"{self.powder.name}_powder.png")

        self.powder.crystal.save_image(filename=path / f"{self.powder.name}.png")

    def plot_point(self):
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
