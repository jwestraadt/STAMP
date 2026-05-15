"""Descriptive statistics and distribution fitting for microstructural data."""

from __future__ import annotations

import numpy as np
from scipy import stats as scipy_stats
from scipy.stats import gaussian_kde

from stamp._types import (
    DescribeResult,
    FitResult,
    MeanResult,
    MeasurementData,
    MedianResult,
    PeakResult,
    _coerce_to_measurement,
)

_VALID_AMEAN_METHODS = ("ASTM", "GCI", "mCox")
_VALID_GMEAN_METHODS = ("CLT", "bayes")
_VALID_DISTRIBUTIONS = ("normal", "lognormal")
_GCI_RUNS = 10_000


def amean(
    data: MeasurementData,
    ci: float = 0.95,
    method: str = "ASTM",
) -> MeanResult:
    """Arithmetic mean with confidence interval.

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Input measurements.  A single-column :class:`~pandas.DataFrame`
        returned by :func:`stamp.io.load` is accepted directly.
    ci : float, optional
        Confidence level in (0, 1).  Default 0.95.
    method : str, optional
        CI method: ``"ASTM"`` (t-distribution, ASTM E112-12),
        ``"GCI"`` (Monte Carlo generalised CI), or
        ``"mCox"`` (Modified Cox, robust for lognormal data).
        Default ``"ASTM"``.

    Returns
    -------
    MeanResult

    Raises
    ------
    ValueError
        If *method* is unknown or *ci* is outside (0, 1).
    """
    data = _coerce_to_measurement(data)
    _validate_ci(ci)
    if method not in _VALID_AMEAN_METHODS:
        raise ValueError(
            f"method must be one of {_VALID_AMEAN_METHODS}, got {method!r}."
        )

    v = data.values
    n = len(v)
    mu = float(np.mean(v))
    sd = float(np.std(v, ddof=1))

    if method == "ASTM":
        lo, hi = _astm_ci(mu, sd, n, ci)
    elif method == "GCI":
        lo, hi = _gci_ci(v, ci)
    else:
        lo, hi = _mcox_ci(v, ci)

    return MeanResult(
        mean=mu,
        std=sd,
        ci_low=lo,
        ci_high=hi,
        ci_length=hi - lo,
        n=n,
        unit=data.unit,
        label=data.label,
    )


def gmean(
    data: MeasurementData,
    ci: float = 0.95,
    method: str = "CLT",
) -> MeanResult:
    """Geometric mean with confidence interval.

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Input measurements (all values must be positive).  A single-column
        :class:`~pandas.DataFrame` returned by :func:`stamp.io.load` is
        accepted directly.
    ci : float, optional
        Confidence level in (0, 1).  Default 0.95.
    method : str, optional
        CI method: ``"CLT"`` (CLT on log-transformed data) or
        ``"bayes"`` (Bayesian via ``scipy.stats.bayes_mvs``).
        Default ``"CLT"``.

    Returns
    -------
    MeanResult
        ``std`` field holds the multiplicative standard deviation
        (i.e. exp(σ_log)).

    Raises
    ------
    ValueError
        If *method* is unknown or *ci* is outside (0, 1).
    """
    data = _coerce_to_measurement(data)
    _validate_ci(ci)
    if method not in _VALID_GMEAN_METHODS:
        raise ValueError(
            f"method must be one of {_VALID_GMEAN_METHODS}, got {method!r}."
        )

    v = data.values
    n = len(v)
    log_v = np.log(v)
    geo_mean = float(np.exp(np.mean(log_v)))
    mult_sd = float(np.exp(np.std(log_v, ddof=1)))

    if method == "CLT":
        lo, hi = _clt2_ci(np.mean(log_v), np.std(log_v, ddof=1), n, ci)
    else:
        lo, hi = _bayesian_ci(log_v, ci)

    return MeanResult(
        mean=geo_mean,
        std=mult_sd,
        ci_low=lo,
        ci_high=hi,
        ci_length=hi - lo,
        n=n,
        unit=data.unit,
        label=data.label,
    )


def median(
    data: MeasurementData,
    ci: float = 0.95,
) -> MedianResult:
    """Median with interquartile range and confidence interval.

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Input measurements.  A single-column :class:`~pandas.DataFrame`
        returned by :func:`stamp.io.load` is accepted directly.
    ci : float, optional
        Confidence level in (0, 1).  Default 0.95.

    Returns
    -------
    MedianResult

    Notes
    -----
    CI uses the Hollander & Wolfe (1999) rule-of-thumb:
    index = (n/2) ± (z × √n) / 2.
    """
    data = _coerce_to_measurement(data)
    _validate_ci(ci)
    v = np.sort(data.values)
    n = len(v)
    med = float(np.median(v))
    q25, q75 = float(np.percentile(v, 25)), float(np.percentile(v, 75))
    iqr = q75 - q25

    z = float(scipy_stats.norm.ppf(1 - (1 - ci) / 2))
    half = z * np.sqrt(n) / 2.0
    lo_idx = max(0, int(np.floor(n / 2 - half)) - 1)
    hi_idx = min(n - 1, int(np.ceil(n / 2 + half)))
    lo, hi = float(v[lo_idx]), float(v[hi_idx])

    return MedianResult(
        median=med,
        iqr=iqr,
        ci_low=lo,
        ci_high=hi,
        ci_length=hi - lo,
        n=n,
        unit=data.unit,
        label=data.label,
    )


def freq_peak(
    data: MeasurementData,
    bandwidth: str | float = "silverman",
) -> PeakResult:
    """Estimate the distribution mode using Gaussian kernel density estimation.

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Input measurements.  A single-column :class:`~pandas.DataFrame`
        returned by :func:`stamp.io.load` is accepted directly.
    bandwidth : str or float, optional
        KDE bandwidth: ``"silverman"``, ``"scott"``, or a positive float.
        Default ``"silverman"``.

    Returns
    -------
    PeakResult

    Raises
    ------
    ValueError
        If *bandwidth* is an unknown string or a non-positive float.
    """
    data = _coerce_to_measurement(data)
    if isinstance(bandwidth, str):
        if bandwidth not in ("silverman", "scott"):
            raise ValueError(
                f"bandwidth must be 'silverman', 'scott', or a positive float, "
                f"got {bandwidth!r}."
            )
        bw_method: str | float = bandwidth
    else:
        bw = float(bandwidth)
        if bw <= 0:
            raise ValueError(f"bandwidth must be positive, got {bw}.")
        bw_method = bw

    v = data.values
    kde = gaussian_kde(v, bw_method=bw_method)
    xgrid = np.linspace(v.min(), v.max(), 512)
    density = kde(xgrid)
    peak_idx = int(np.argmax(density))
    resolved_bw = float(kde.factor * np.std(v, ddof=1))

    return PeakResult(
        peak=float(xgrid[peak_idx]),
        peak_density=float(density[peak_idx]),
        xgrid=xgrid,
        density=density,
        bandwidth=resolved_bw,
        unit=data.unit,
        label=data.label,
    )


def fit(
    data: MeasurementData,
    distribution: str = "lognormal",
) -> FitResult:
    """Fit a parametric distribution via maximum likelihood estimation.

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Input measurements.  A single-column :class:`~pandas.DataFrame`
        returned by :func:`stamp.io.load` is accepted directly.
    distribution : str, optional
        ``"normal"`` or ``"lognormal"``.  Default ``"lognormal"``.

    Returns
    -------
    FitResult

    Raises
    ------
    ValueError
        If *distribution* is not ``"normal"`` or ``"lognormal"``.
    RuntimeError
        If MLE optimisation fails to converge.
    """
    data = _coerce_to_measurement(data)
    if distribution not in _VALID_DISTRIBUTIONS:
        raise ValueError(
            f"distribution must be one of {_VALID_DISTRIBUTIONS}, got {distribution!r}."
        )

    v = data.values

    try:
        if distribution == "normal":
            loc, scale = scipy_stats.norm.fit(v)
            params = {"loc": float(loc), "scale": float(scale)}
            dist_obj = scipy_stats.norm(loc=loc, scale=scale)
        else:
            s, loc, scale = scipy_stats.lognorm.fit(v, floc=0)
            params = {"s": float(s), "loc": float(loc), "scale": float(scale)}
            dist_obj = scipy_stats.lognorm(s=s, loc=loc, scale=scale)
    except Exception as exc:
        raise RuntimeError(f"MLE fitting failed: {exc}") from exc

    # Goodness of fit
    ks_stat, ks_p = scipy_stats.kstest(v, dist_obj.cdf)
    empirical_cdf = np.arange(1, len(v) + 1) / len(v)
    fitted_cdf = dist_obj.cdf(np.sort(v))
    ss_res = np.sum((empirical_cdf - fitted_cdf) ** 2)
    ss_tot = np.sum((empirical_cdf - np.mean(empirical_cdf)) ** 2)
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return FitResult(
        distribution=distribution,
        params=params,
        r_squared=r2,
        ks_statistic=float(ks_stat),
        ks_pvalue=float(ks_p),
        unit=data.unit,
        label=data.label,
    )


def describe(
    data: MeasurementData,
    ci: float = 0.95,
) -> DescribeResult:
    """Convenience wrapper: compute all standard descriptive statistics.

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Input measurements.  A single-column :class:`~pandas.DataFrame`
        returned by :func:`stamp.io.load` is accepted directly.
    ci : float, optional
        Confidence level passed to all sub-functions.  Default 0.95.

    Returns
    -------
    DescribeResult
    """
    data = _coerce_to_measurement(data)
    percentile_keys = [5, 10, 25, 75, 90, 95]
    pcts = {k: float(np.percentile(data.values, k)) for k in percentile_keys}

    return DescribeResult(
        n=len(data.values),
        amean=amean(data, ci=ci, method="ASTM"),
        gmean=gmean(data, ci=ci, method="CLT"),
        median=median(data, ci=ci),
        peak=freq_peak(data, bandwidth="silverman"),
        percentiles=pcts,
        unit=data.unit,
        label=data.label,
    )


# ---------------------------------------------------------------------------
# CI helpers
# ---------------------------------------------------------------------------


def _validate_ci(ci: float) -> None:
    if not (0 < ci < 1):
        raise ValueError(f"ci must be in (0, 1), got {ci}.")


def _astm_ci(mean: float, std: float, n: int, ci: float) -> tuple[float, float]:
    """t-distribution CI per ASTM E112-12."""
    t = float(scipy_stats.t.ppf(1 - (1 - ci) / 2, df=n - 1))
    err = t * std / np.sqrt(n)
    return mean - err, mean + err


def _gci_ci(v: np.ndarray, ci: float, runs: int = _GCI_RUNS) -> tuple[float, float]:
    """Monte Carlo generalised confidence interval (Krishnamoorthy & Mathew 2003)."""
    n = len(v)
    mu_log = np.mean(np.log(v))
    var_log = np.var(np.log(v), ddof=1)
    rng = np.random.default_rng(0)
    z = rng.standard_normal(runs)
    u = rng.chisquare(n - 1, size=runs)
    # GCI T-values (applied to original scale via arithmetic mean)
    t_vals = np.exp(mu_log + np.sqrt(var_log / n) * z) * np.exp(
        var_log * (1 - (n - 1) / u) / 2
    )
    alpha = (1 - ci) / 2
    lo = float(np.percentile(t_vals, 100 * alpha))
    hi = float(np.percentile(t_vals, 100 * (1 - alpha)))
    return lo, hi


def _mcox_ci(v: np.ndarray, ci: float) -> tuple[float, float]:
    """Modified Cox method (Armstrong 1992)."""
    n = len(v)
    mu_log = np.mean(np.log(v))
    var_log = np.var(np.log(v), ddof=1)
    t = float(scipy_stats.t.ppf(1 - (1 - ci) / 2, df=n - 1))
    err = t * np.sqrt(var_log / n + var_log**2 / (2 * (n - 1)))
    lo = np.exp(mu_log + var_log / 2 - err)
    hi = np.exp(mu_log + var_log / 2 + err)
    return float(lo), float(hi)


def _clt2_ci(mean_log: float, std_log: float, n: int, ci: float) -> tuple[float, float]:
    """CLT on log-transformed data, back-transformed (for geometric mean)."""
    t = float(scipy_stats.t.ppf(1 - (1 - ci) / 2, df=n - 1))
    err = t * std_log / np.sqrt(n)
    return float(np.exp(mean_log - err)), float(np.exp(mean_log + err))


def _bayesian_ci(log_v: np.ndarray, ci: float) -> tuple[float, float]:
    """Bayesian CI via scipy.stats.bayes_mvs on log data (Oliphant 2006)."""
    mean_ci, _, _ = scipy_stats.bayes_mvs(log_v, alpha=ci)
    lo = float(np.exp(mean_ci.minmax[0]))
    hi = float(np.exp(mean_ci.minmax[1]))
    return lo, hi
