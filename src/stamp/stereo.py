"""Stereological corrections for 2-D microstructural measurements."""

from __future__ import annotations

import warnings

import numpy as np
from scipy.optimize import curve_fit

from stamp._types import MeasurementData, SaltykovResult, TwoStepResult

_SALTYKOV_N_BINS_MIN = 3
_SALTYKOV_N_BINS_MAX = 25


def ecd_from_area(data: MeasurementData) -> MeasurementData:
    """Convert 2-D projected areas to equivalent circle diameters (ECD).

    Parameters
    ----------
    data : MeasurementData
        Measured grain or precipitate areas.  The ``unit`` string should be a
        length-squared unit (e.g. ``"µm²"``), though this is not enforced.

    Returns
    -------
    MeasurementData
        Equivalent circle diameters.  The unit is derived by stripping a
        trailing ``²`` character (``"µm²"`` → ``"µm"``); if no ``²`` is
        present the unit is kept unchanged.  The label is set to ``"ECD"``.

    Notes
    -----
    Formula: ECD = 2 × √(area / π)
    """
    ecds = 2.0 * np.sqrt(data.values / np.pi)
    new_unit = data.unit.rstrip("²") if data.unit.endswith("²") else data.unit
    return MeasurementData(values=ecds, unit=new_unit, label="ECD")


def linear_intercept_correction(data: MeasurementData) -> MeasurementData:
    """Apply the Fullman (1953) correction to convert 2-D linear intercept lengths
    to estimated 3-D grain diameters, assuming equiaxed grains (ASTM E112).

    Parameters
    ----------
    data : MeasurementData
        Linear intercept chord lengths.

    Returns
    -------
    MeasurementData
        Corrected grain diameters with label ``"Corrected Grain Diameter"``.

    Notes
    -----
    Formula: D = (4 / π) × L, applied element-wise.
    The correction factor 4/π ≈ 1.273 assumes equiaxed grains.
    """
    corrected = data.values * (4.0 / np.pi)
    return MeasurementData(
        values=corrected,
        unit=data.unit,
        label="Corrected Grain Diameter",
    )


def saltykov(
    data: MeasurementData,
    n_bins: int = 10,
    left_edge: float | str = 0,
) -> SaltykovResult:
    """Convert a 2-D circle-diameter distribution to a 3-D sphere-diameter
    distribution using the Saltykov (1967) matrix unfolding method.

    Parameters
    ----------
    data : MeasurementData
        2-D circle diameters (e.g. from :func:`ecd_from_area`).
    n_bins : int, optional
        Number of equal-width bins; must be in [3, 25].  Default 10.
    left_edge : float or ``"min"``, optional
        Lower histogram bound.  Pass ``"min"`` to use the data minimum.
        Default 0.

    Returns
    -------
    SaltykovResult
        Contains bin midpoints, bin edges, bin width, normalised 3-D
        frequency density, and volume-weighted cumulative distribution.

    Raises
    ------
    ValueError
        If *n_bins* is outside [3, 25] or fewer unique values exist than bins.

    Notes
    -----
    Implements Wicksell's (1925) cross-section probability:

        P(r₁ < r < r₂ | R) = (1/R) × [√(R²−r₁²) − √(R²−r₂²)]

    References
    ----------
    Saltykov (1967); Wicksell (1925); Sahagian & Proussevitch (1998);
    Higgins (2000).
    """
    if not (_SALTYKOV_N_BINS_MIN <= n_bins <= _SALTYKOV_N_BINS_MAX):
        raise ValueError(
            f"n_bins must be between {_SALTYKOV_N_BINS_MIN} and "
            f"{_SALTYKOV_N_BINS_MAX}, got {n_bins}."
        )

    diameters = data.values
    if left_edge == "min":
        start = diameters.min()
    else:
        start = float(left_edge)

    bin_width = (diameters.max() - start) / n_bins
    bin_edges = np.linspace(start, diameters.max(), n_bins + 1)
    bin_midpoints = bin_edges[:-1] + bin_width / 2.0

    freq2d, _ = np.histogram(diameters, bins=bin_edges)
    freq2d = freq2d.astype(float)

    freq3d = _unfold_population(freq2d, bin_edges, bin_width, bin_midpoints)
    cdf_vol = _volume_weighted_cdf(freq3d, bin_midpoints)

    return SaltykovResult(
        bin_midpoints=bin_midpoints,
        bin_edges=bin_edges,
        bin_width=bin_width,
        freq3d=freq3d,
        cdf_vol=cdf_vol,
        unit=data.unit,
        label=data.label,
    )


def _wicksell(diameter: float, lower: float, upper: float) -> float:
    """Wicksell cross-section probability for a sphere of given diameter."""
    r = diameter / 2.0
    r1 = lower / 2.0
    r2 = upper / 2.0
    if r <= r1:
        return 0.0
    r2_clamped = min(r2, r)
    return (1.0 / r) * (
        np.sqrt(max(r**2 - r1**2, 0.0)) - np.sqrt(max(r**2 - r2_clamped**2, 0.0))
    )


def _unfold_population(
    freq2d: np.ndarray,
    bin_edges: np.ndarray,
    bin_width: float,
    bin_midpoints: np.ndarray,
    normalize: bool = True,
) -> np.ndarray:
    """Iterative Saltykov unfolding from coarsest to finest class."""
    n = len(freq2d)
    freq3d = np.zeros(n)

    for i in range(n - 1, -1, -1):
        # Subtract contributions of already-estimated coarser classes
        correction = sum(
            freq3d[j] * _wicksell(bin_midpoints[j], bin_edges[i], bin_edges[i + 1])
            for j in range(i + 1, n)
        )
        raw = (freq2d[i] - correction * bin_width) / bin_width
        freq3d[i] = raw

    if normalize:
        n_neg = int(np.sum(freq3d < 0))
        if n_neg > 0:
            warnings.warn(
                f"{n_neg} bin(s) had negative unfolded frequencies "
                "and were clipped to zero.",
                UserWarning,
                stacklevel=4,
            )
        freq3d = np.clip(freq3d, 0.0, None)
        total = np.sum(freq3d) * bin_width
        if total > 0:
            freq3d /= total

    return freq3d


def _volume_weighted_cdf(freq3d: np.ndarray, bin_midpoints: np.ndarray) -> np.ndarray:
    """Volume-weighted cumulative distribution normalised to 100 %."""
    vol_weighted = freq3d * bin_midpoints**3
    cumulative = np.cumsum(vol_weighted)
    total = cumulative[-1]
    if total > 0:
        return cumulative / total * 100.0
    return cumulative


def two_step(
    data: MeasurementData,
    bin_range: tuple[int, int] = (10, 20),
) -> TwoStepResult:
    """Estimate the best-fit lognormal for a 3-D grain size distribution.

    Iterates the Saltykov unfolding over a range of bin counts, fits a
    lognormal PDF to each result, and selects the bin count that minimises
    the residual sum of squares.  Follows Lopez-Sanchez & Llana-Funez (2016).

    Parameters
    ----------
    data : MeasurementData
        2-D circle diameters.
    bin_range : tuple of int, optional
        Inclusive ``(min, max)`` range of bin counts to test.  Default
        ``(10, 20)``.

    Returns
    -------
    TwoStepResult

    Raises
    ------
    ValueError
        If *bin_range* is invalid or values fall outside [3, 25].
    RuntimeError
        If lognormal fitting fails to converge for all bin counts.

    References
    ----------
    Lopez-Sanchez & Llana-Funez (2016) *Solid Earth* 7, 1197–1212.
    """
    lo, hi = bin_range
    if lo >= hi:
        raise ValueError(f"bin_range min must be less than max, got {bin_range}.")
    if lo < _SALTYKOV_N_BINS_MIN or hi > _SALTYKOV_N_BINS_MAX:
        raise ValueError(
            f"bin_range values must be within [{_SALTYKOV_N_BINS_MIN}, "
            f"{_SALTYKOV_N_BINS_MAX}], got {bin_range}."
        )

    best_ssr = np.inf
    best_params = None
    best_pcov = None
    best_n_bins = lo
    best_sal = None

    for n in range(lo, hi + 1):
        sal = saltykov(data, n_bins=n)
        if np.all(sal.freq3d == 0):
            continue
        # Initial guess: shape from log-std, scale from median
        log_vals = np.log(data.values)
        shape0 = np.exp(np.std(log_vals))
        scale0 = np.median(data.values)
        try:
            popt, pcov = curve_fit(
                _lognormal_pdf,
                sal.bin_midpoints,
                sal.freq3d,
                p0=[shape0, scale0],
                bounds=([1.0, 0.0], [10.0, np.inf]),
                maxfev=10000,
            )
        except RuntimeError:
            continue
        residuals = sal.freq3d - _lognormal_pdf(sal.bin_midpoints, *popt)
        ssr = float(np.sum(residuals**2))
        if ssr < best_ssr:
            best_ssr = ssr
            best_params = popt
            best_pcov = pcov
            best_n_bins = n
            best_sal = sal

    if best_params is None:
        raise RuntimeError(
            "Lognormal fitting failed to converge for all bin counts in range."
        )

    shape, scale = best_params
    params_err = np.sqrt(np.diag(best_pcov))

    xgrid = np.linspace(best_sal.bin_edges[0], best_sal.bin_edges[-1], 300)
    fit_curve = _lognormal_pdf(xgrid, shape, scale)

    # ±3σ uncertainty band from parameter covariance
    sh_lo, sc_lo = best_params - 3 * params_err
    sh_hi, sc_hi = best_params + 3 * params_err
    sh_lo = max(sh_lo, 1.001)
    sc_lo = max(sc_lo, 1e-9)
    curve_lo = _lognormal_pdf(xgrid, sh_lo, sc_lo)
    curve_hi = _lognormal_pdf(xgrid, sh_hi, sc_hi)
    fit_error = np.abs(curve_hi - curve_lo) / 2.0

    return TwoStepResult(
        geometric_mean=float(scale),
        shape=float(shape),
        params_err=params_err,
        best_n_bins=best_n_bins,
        xgrid=xgrid,
        fit_curve=fit_curve,
        fit_error=fit_error,
        unit=data.unit,
        label=data.label,
    )


def _lognormal_pdf(x: np.ndarray, shape: float, scale: float) -> np.ndarray:
    """Two-parameter lognormal PDF; shape = multiplicative σ, scale = geometric mean."""
    s = np.log(shape)
    m = np.log(scale)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = (1.0 / (x * s * np.sqrt(2 * np.pi))) * np.exp(
            -0.5 * ((np.log(x) - m) / s) ** 2
        )
    return np.where(np.isfinite(result), result, 0.0)
