"""
Simplified PowderCell-like implementation in Python
(Error‑free version)
"""

import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize

from src.model.atom.atom import Atom
from src.model.crystal.crystal import Crystal
from src.model.group.space import TrivialSpaceGroup
from src.model.pattern.powder import PowderPattern

# ----------------------------------------------------------------------
# 7. Example: Silicon (cubic, manually placed atoms)
# ----------------------------------------------------------------------
a_Si = 5.4307
atoms_Si = [
    Atom("Si", 0.0, 0.0, 0.0),
    Atom("Si", 0.0, 0.5, 0.5),
    Atom("Si", 0.5, 0.0, 0.5),
    Atom("Si", 0.5, 0.5, 0.0),
    Atom("Si", 0.25, 0.25, 0.25),
    Atom("Si", 0.25, 0.75, 0.75),
    Atom("Si", 0.75, 0.25, 0.75),
    Atom("Si", 0.75, 0.75, 0.25),
]
crystal_Si = Crystal(a_Si, a_Si, a_Si, 90, 90, 90, TrivialSpaceGroup(), atoms_Si)

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
plt.plot(pattern_Si.twotheta, pattern_Si.ycalc, label="Simulated Si")
plt.xlabel("2θ (deg)")
plt.ylabel("Intensity")
plt.title("Simulated powder pattern of Silicon")
plt.legend()
plt.grid(True)
plt.savefig("silicon_pattern.png", dpi=300)
plt.close()


# ----------------------------------------------------------------------
# 8. Refinement framework (simple Rietveld)
# ----------------------------------------------------------------------
def residual(
    params, twotheta_exp, y_exp, crystal_template, wavelength, profile="pvoigt"
):
    """
    Residual function for least-squares refinement.
    params: [scale, U, V, W, eta, a]
    """
    scale, U, V, W, eta, a = params
    # Create a copy of the crystal with the new lattice parameter
    crystal_copy = crystal_template.copy()
    crystal_copy.a = a
    crystal_copy.b = a
    crystal_copy.c = a
    crystal_copy._compute_metrics()
    # Regenerate full atoms (lattice not changed, so same positions)
    crystal_copy.full_atoms = crystal_copy._generate_full_atoms()
    # Compute pattern
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
plt.title("Rietveld refinement test")
plt.legend()
plt.grid(True)
plt.savefig("silicon_patternl.png", dpi=300)
plt.close()
