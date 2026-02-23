"""
Simplified PowderCell-like implementation in Python
(Error‑free version)
"""

import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize

from src.model.atom.atom import Atom
from src.model.crystal.crystal import Crystal, lattice_to_matrix
from src.model.pattern.powder import PowderPattern

a_Si = 5.4307
# Asymmetric unit for Si in Fd-3m (origin choice 2): two independent atoms
atoms_Si = [
    Atom("Si", 0.0, 0.0, 0.0),  # 8a site
    Atom("Si", 0.25, 0.25, 0.25),  # 8b site
]
crystal_Si = Crystal(a_Si, a_Si, a_Si, 90, 90, 90, 227, atoms_Si)

lambda_Cu = 1.54056

pattern_Si = PowderPattern(
    crystal_Si,
    lambda_Cu,
    (20, 100, 0.02),
    U=0.01,
    V=-0.005,
    W=0.005,
    scale=1.0,
    profile="pvoigt",
    eta=0.5,
)

# Plot
plt.figure(figsize=(10, 4))
plt.plot(pattern_Si.twotheta, pattern_Si.ycalc, label="Simulated Si (spglib)")
plt.xlabel("2θ (deg)")
plt.ylabel("Intensity")
plt.title("Simulated powder pattern of Silicon (Fd-3m)")
plt.legend()
plt.grid(True)
plt.savefig("1.png")


# ----------------------------------------------------------------------
# 7. Refinement framework (simple Rietveld)
# ----------------------------------------------------------------------
def residual(
    params, twotheta_exp, y_exp, crystal_template, wavelength, profile="pvoigt"
):
    scale, U, V, W, eta, a = params
    crystal_copy = crystal_template.copy()
    crystal_copy.a = a
    crystal_copy.b = a
    crystal_copy.c = a
    crystal_copy._compute_metrics()
    crystal_copy._lattice_matrix = lattice_to_matrix(a, a, a, 90, 90, 90)
    # Need to regenerate symmetry operations because lattice changed
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


# Create synthetic "experimental" data with noise
y_exp_synth = pattern_Si.ycalc + np.random.normal(
    0, 0.1 * pattern_Si.ycalc.max(), size=len(pattern_Si.twotheta)
)
twotheta_exp = pattern_Si.twotheta

# Initial guess
params0 = [0.9, 0.02, -0.01, 0.008, 0.4, 5.4]

# Refine
result = scipy.optimize.leastsq(
    residual, params0, args=(twotheta_exp, y_exp_synth, crystal_Si, lambda_Cu)
)
params_refined = result[0]

print("Refined parameters:")
print(f"Scale = {params_refined[0]:.4f}")
print(f"U = {params_refined[1]:.4f}")
print(f"V = {params_refined[2]:.4f}")
print(f"W = {params_refined[3]:.4f}")
print(f"eta = {params_refined[4]:.4f}")
print(f"a = {params_refined[5]:.4f}")

# Plot comparison
y_calc_refined = PowderPattern(
    crystal_Si,
    lambda_Cu,
    (20, 100, 0.02),
    U=params_refined[1],
    V=params_refined[2],
    W=params_refined[3],
    scale=params_refined[0],
    eta=params_refined[4],
).ycalc

plt.figure(figsize=(10, 4))
plt.plot(twotheta_exp, y_exp_synth, "k.", markersize=1, label="Exp (synthetic)")
plt.plot(
    twotheta_exp,
    np.interp(twotheta_exp, pattern_Si.twotheta, y_calc_refined),
    "r-",
    label="Refined",
)
plt.xlabel("2θ (deg)")
plt.ylabel("Intensity")
plt.title("Rietveld refinement test with spglib")
plt.legend()
plt.grid(True)
plt.savefig("2.png")
