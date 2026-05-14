"""Synthetic grain size simulation for validating stereological corrections."""

from __future__ import annotations

import warnings

import numpy as np

from stamp._types import MeasurementData, SimulationResult

_VALID_DIST = {"lognormal", "normal"}


def simulate_section(
    mu: float,
    sigma: float,
    n_intersections: int = 500,
    n_grains: int = 10_000,
    distribution: str = "lognormal",
    seed: int | None = None,
    unit: str = "µm",
) -> SimulationResult:
    """Generate a synthetic mono-modal 3-D grain population and simulate random
    2-D cross-sections using the Wicksell (1925) corpuscle model.

    Parameters
    ----------
    mu : float
        Geometric mean diameter for ``"lognormal"``; arithmetic mean for
        ``"normal"``.  Must be positive.
    sigma : float
        Log-scale shape parameter (σ of ln D) for ``"lognormal"``; standard
        deviation for ``"normal"``.  Must be positive.
    n_intersections : int, optional
        Number of 2-D apparent diameter measurements to generate.  Default 500.
    n_grains : int, optional
        Size of the 3-D grain pool.  Must be ≥ ``n_intersections``.
        Default 10 000.
    distribution : str, optional
        Parent distribution: ``"lognormal"`` or ``"normal"``.
        Default ``"lognormal"``.
    seed : int or None, optional
        NumPy random seed for reproducibility.  Default ``None``.
    unit : str, optional
        Physical unit string for both output ``MeasurementData`` objects.
        Default ``"µm"``.

    Returns
    -------
    SimulationResult

    Raises
    ------
    ValueError
        If *distribution* is not ``"lognormal"`` or ``"normal"``.
    ValueError
        If *mu* ≤ 0, *sigma* ≤ 0, *n_intersections* < 1, or
        *n_grains* < *n_intersections*.

    Notes
    -----
    **Wicksell corpuscle algorithm**:

    1. Draw ``n_grains`` sphere diameters D_i from the chosen distribution.
    2. Assign sampling weight w_i = D_i (larger spheres intersect a random
       plane with probability proportional to their diameter).
    3. For each of ``n_intersections`` measurements: sample grain *i* with
       probability ∝ w_i, draw *t* ~ Uniform(0, D_i / 2), and record
       apparent circle diameter d = 2 √((D_i / 2)² − t²).

    For ``"lognormal"``, *mu* is the geometric mean (scale = exp(μ_log)) and
    *sigma* is the standard deviation of ln D.  Typical metallurgical /
    geological values: σ ≈ 0.2–0.5.

    References
    ----------
    Wicksell SD (1925) *Biometrika* 17, 84–99.
    """
    if distribution not in _VALID_DIST:
        raise ValueError(
            f"distribution must be one of {_VALID_DIST}, got {distribution!r}."
        )
    if mu <= 0:
        raise ValueError(f"mu must be positive, got {mu}.")
    if sigma <= 0:
        raise ValueError(f"sigma must be positive, got {sigma}.")
    if n_intersections < 1:
        raise ValueError(f"n_intersections must be >= 1, got {n_intersections}.")
    if n_grains < n_intersections:
        raise ValueError(
            f"n_grains ({n_grains}) must be >= n_intersections ({n_intersections})."
        )

    rng = np.random.default_rng(seed)

    # ── 1. Draw the 3-D grain pool ────────────────────────────────────────────
    if distribution == "lognormal":
        mu_log = np.log(mu)
        diameters_3d = rng.lognormal(mean=mu_log, sigma=sigma, size=n_grains)
    else:
        diameters_3d = rng.normal(loc=mu, scale=sigma, size=n_grains)
        n_negative = int(np.sum(diameters_3d <= 0))
        if n_negative > 0:
            rejection_rate = n_negative / n_grains
            if rejection_rate > 0.01:
                warnings.warn(
                    f"Normal distribution: {rejection_rate:.1%} of draws were "
                    "non-positive and were redrawn. Consider a larger mu/sigma ratio.",
                    UserWarning,
                    stacklevel=2,
                )
            while np.any(diameters_3d <= 0):
                mask = diameters_3d <= 0
                diameters_3d[mask] = rng.normal(
                    loc=mu, scale=sigma, size=int(mask.sum())
                )

    # ── 2. Wicksell sectioning ────────────────────────────────────────────────
    # Sampling probability ∝ D_i: larger spheres are more likely to be cut
    weights = diameters_3d / diameters_3d.sum()
    chosen_idx = rng.choice(n_grains, size=n_intersections, replace=True, p=weights)
    d_chosen = diameters_3d[chosen_idx]
    r_chosen = d_chosen / 2.0
    # Perpendicular distance from sphere centre to cutting plane
    t = rng.uniform(0.0, r_chosen)
    apparent = 2.0 * np.sqrt(np.maximum(r_chosen**2 - t**2, 0.0))

    true_data = MeasurementData(
        values=diameters_3d,
        unit=unit,
        label="True 3D Diameter",
    )
    apparent_data = MeasurementData(
        values=apparent,
        unit=unit,
        label="Apparent 2D Diameter",
    )

    return SimulationResult(
        true_diameters=true_data,
        apparent_diameters=apparent_data,
        mu=mu,
        sigma=sigma,
        distribution=distribution,
        n_grains=n_grains,
        n_intersections=n_intersections,
        unit=unit,
        seed=seed,
    )
