"""Stereological corrections for 2-D microstructural measurements."""

from __future__ import annotations

import warnings

import numpy as np
from scipy.optimize import curve_fit

from stamp._types import (
    MeasurementData,
    SaltykovResult,
    TwoStepResult,
    _coerce_to_measurement,
)

_SALTYKOV_N_BINS_MIN = 3
_SALTYKOV_N_BINS_MAX = 25


def ecd_from_area(data: MeasurementData) -> MeasurementData:
    """Convert 2-D projected areas to equivalent circle diameters (ECD).

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Measured grain or precipitate areas.  The ``unit`` string should be a
        length-squared unit (e.g. ``"µm²"``), though this is not enforced.
        A single-column :class:`~pandas.DataFrame` from :func:`stamp.io.load`
        is accepted directly.

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
    data = _coerce_to_measurement(data)
    ecds = 2.0 * np.sqrt(data.values / np.pi)
    new_unit = data.unit.rstrip("²") if data.unit.endswith("²") else data.unit
    return MeasurementData(values=ecds, unit=new_unit, label="ECD")


def linear_intercept_correction(data: MeasurementData) -> MeasurementData:
    """Apply the Fullman (1953) correction to convert 2-D linear intercept lengths
    to estimated 3-D grain diameters, assuming equiaxed grains (ASTM E112).

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Linear intercept chord lengths.  A single-column
        :class:`~pandas.DataFrame` from :func:`stamp.io.load` is accepted
        directly.

    Returns
    -------
    MeasurementData
        Corrected grain diameters with label ``"Corrected Grain Diameter"``.

    Notes
    -----
    Formula: D = (4 / π) × L, applied element-wise.
    The correction factor 4/π ≈ 1.273 assumes equiaxed grains.
    """
    data = _coerce_to_measurement(data)
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
    data : MeasurementData, pd.DataFrame, or pd.Series
        2-D circle diameters (e.g. from :func:`ecd_from_area`).  A
        single-column :class:`~pandas.DataFrame` from :func:`stamp.io.load`
        is accepted directly.
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
    data = _coerce_to_measurement(data)
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
    data : MeasurementData, pd.DataFrame, or pd.Series
        2-D circle diameters.  A single-column :class:`~pandas.DataFrame`
        from :func:`stamp.io.load` is accepted directly.
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
    data = _coerce_to_measurement(data)
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


# ---------------------------------------------------------------------------
# Image-level stereological quantities
# ---------------------------------------------------------------------------


def volume_fraction(
    area_fraction_pct: float | np.ndarray,
) -> float | np.ndarray:
    """Convert areal fraction (%) to volume fraction via the Delesse principle.

    Parameters
    ----------
    area_fraction_pct : float or np.ndarray
        Areal phase fraction in percent, as reported by MIPAR
        (``"Area Fraction (%)"``) or equivalent image analysis software.
        Must be in [0, 100]; NaN values are passed through.

    Returns
    -------
    float or np.ndarray
        Volume fraction $V_V$ in [0, 1] (dimensionless).  Scalar input
        returns a scalar; array input returns an array of the same shape.

    Raises
    ------
    ValueError
        If any non-NaN value falls outside [0, 100].

    Notes
    -----
    Delesse (1848) showed that the areal fraction of a phase on a random
    planar section equals its volume fraction: $V_V = A_A$.

    References
    ----------
    Delesse, A. (1848) *Ann. Mines* 13, 379–388.

    Examples
    --------
    >>> volume_fraction(5.0)
    0.05
    >>> volume_fraction(np.array([0.0, 5.0, 100.0]))
    array([0.  , 0.05, 1.  ])
    """
    arr = np.asarray(area_fraction_pct, dtype=float)
    valid = arr[~np.isnan(arr)]
    if valid.size > 0 and (np.any(valid < 0) or np.any(valid > 100)):
        raise ValueError(
            "area_fraction_pct must be in [0, 100]; got values outside this range."
        )
    result = arr / 100.0
    return float(result) if result.ndim == 0 else result


def surface_area_density(
    vv: float | np.ndarray,
    l_alpha_um: float | np.ndarray,
) -> float | np.ndarray:
    """Estimate the surface area density $S_V$ from volume fraction and mean intercept.

    Parameters
    ----------
    vv : float or np.ndarray
        Volume fraction (dimensionless, in [0, 1]).  Obtain from
        :func:`volume_fraction` or directly from the area fraction.
    l_alpha_um : float or np.ndarray
        Mean intercept length through the phase of interest (µm), e.g.
        MIPAR's ``"Mean Intercept - Objects (Random) (um)"``.
        Must be > 0; NaN values are passed through.

    Returns
    -------
    float or np.ndarray
        Surface area density $S_V$ in µm⁻¹.  Scalar input returns a scalar;
        array input returns an array of the same shape.

    Raises
    ------
    ValueError
        If any non-NaN value of *l_alpha_um* is ≤ 0.

    Notes
    -----
    From Underwood (1970), for isotropic test lines:

    .. math:: S_V = \\frac{4\\,V_V}{\\bar{L}_\\alpha}

    where $\\bar{L}_\\alpha$ is the mean intercept length through the phase.

    References
    ----------
    Underwood, E.E. (1970) *Quantitative Stereology*. Addison-Wesley.

    Examples
    --------
    >>> surface_area_density(0.05, 0.5)
    0.4
    """
    l_arr = np.asarray(l_alpha_um, dtype=float)
    valid_l = l_arr[~np.isnan(l_arr)]
    if valid_l.size > 0 and np.any(valid_l <= 0):
        raise ValueError("l_alpha_um must be > 0; got values ≤ 0.")
    result = 4.0 * np.asarray(vv, dtype=float) / l_arr
    return float(result) if result.ndim == 0 else result


def mean_caliper_diameter(
    l_alpha_um: float | np.ndarray,
) -> float | np.ndarray:
    """Estimate the mean caliper (particle) diameter from the mean intercept length.

    Parameters
    ----------
    l_alpha_um : float or np.ndarray
        Mean intercept length through the phase of interest (µm), e.g.
        MIPAR's ``"Mean Intercept - Objects (Random) (um)"``.
        Must be > 0; NaN values are passed through.

    Returns
    -------
    float or np.ndarray
        Mean caliper diameter $\\bar{D}$ in µm.  Scalar input returns a
        scalar; array input returns an array of the same shape.

    Raises
    ------
    ValueError
        If any non-NaN value of *l_alpha_um* is ≤ 0.

    Notes
    -----
    Fullman (1953) showed that for convex, equiaxed particles:

    .. math:: \\bar{D} = \\frac{3}{2}\\,\\bar{L}_\\alpha

    The factor 3/2 is exact for spheres and a good approximation for
    near-equiaxed precipitates.

    References
    ----------
    Fullman, R.L. (1953) *Trans. AIME* 197, 447–452.

    Examples
    --------
    >>> mean_caliper_diameter(0.5)
    0.75
    """
    l_arr = np.asarray(l_alpha_um, dtype=float)
    valid_l = l_arr[~np.isnan(l_arr)]
    if valid_l.size > 0 and np.any(valid_l <= 0):
        raise ValueError("l_alpha_um must be > 0; got values ≤ 0.")
    result = 1.5 * l_arr
    return float(result) if result.ndim == 0 else result


def mean_free_path_3d(
    vv: float | np.ndarray,
    sv: float | np.ndarray,
) -> float | np.ndarray:
    """Estimate the 3-D mean free path (interparticle spacing) from $S_V$ and $V_V$.

    Parameters
    ----------
    vv : float or np.ndarray
        Volume fraction (dimensionless, in [0, 1)).  Obtain from
        :func:`volume_fraction`.
    sv : float or np.ndarray
        Surface area density (µm⁻¹).  Obtain from :func:`surface_area_density`.
        Must be > 0; NaN values are passed through.

    Returns
    -------
    float or np.ndarray
        3-D mean free path $\\lambda_{3D}$ in µm.  Scalar input returns a
        scalar; array input returns an array of the same shape.

    Raises
    ------
    ValueError
        If any non-NaN value of *sv* is ≤ 0.

    Notes
    -----
    From Underwood (1970):

    .. math:: \\lambda_{3D} = \\frac{4\\,(1-V_V)}{S_V}

    For isotropic microstructures this equals the mean intercept length
    through the matrix phase ($\\bar{L}_\\beta$), which MIPAR measures
    directly as *Mean Intercept – Holes (Random)*.

    References
    ----------
    Underwood, E.E. (1970) *Quantitative Stereology*. Addison-Wesley.

    Examples
    --------
    >>> mean_free_path_3d(0.05, 0.4)
    9.5
    """
    sv_arr = np.asarray(sv, dtype=float)
    valid_sv = sv_arr[~np.isnan(sv_arr)]
    if valid_sv.size > 0 and np.any(valid_sv <= 0):
        raise ValueError("sv must be > 0; got values ≤ 0.")
    result = 4.0 * (1.0 - np.asarray(vv, dtype=float)) / sv_arr
    return float(result) if result.ndim == 0 else result
