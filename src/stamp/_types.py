"""Shared dataclasses used across all stamp modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class MeasurementData:
    """Container for a 1-D array of positive measurements with unit metadata.

    Parameters
    ----------
    values : np.ndarray
        1-D array of finite, positive float64 values.
    unit : str
        Physical unit string, e.g. ``"µm"`` or ``"µm²"``.
    label : str
        Human-readable feature name, e.g. ``"Grain ECD"``.
    """

    values: np.ndarray
    unit: str
    label: str

    def __post_init__(self) -> None:
        self.values = np.asarray(self.values, dtype=np.float64)
        if self.values.ndim != 1:
            raise ValueError("values must be 1-D.")
        if not self.unit:
            raise ValueError("unit must be a non-empty string.")


# ---------------------------------------------------------------------------
# Stereology results
# ---------------------------------------------------------------------------


@dataclass
class SaltykovResult:
    """Output of :func:`stamp.stereo.saltykov`.

    Parameters
    ----------
    bin_midpoints : np.ndarray
        Bin centre diameters for the 3-D sphere distribution.
    bin_edges : np.ndarray
        Bin edges (length ``n_bins + 1``).
    bin_width : float
        Constant bin width.
    freq3d : np.ndarray
        Normalised 3-D frequency density (integrates to ~1).
    cdf_vol : np.ndarray
        Volume-weighted cumulative distribution in percent (0–100).
    unit : str
        Inherited unit string.
    label : str
        Inherited label string.
    """

    bin_midpoints: np.ndarray
    bin_edges: np.ndarray
    bin_width: float
    freq3d: np.ndarray
    cdf_vol: np.ndarray
    unit: str
    label: str


@dataclass
class TwoStepResult:
    """Output of :func:`stamp.stereo.two_step`.

    Parameters
    ----------
    geometric_mean : float
        Scale parameter (geometric mean) of the best-fit lognormal.
    shape : float
        Multiplicative standard deviation (σ of ln-transformed data).
    params_err : np.ndarray
        1-σ uncertainties on ``[shape, scale]``.
    best_n_bins : int
        Bin count that produced the minimum fitting error.
    xgrid : np.ndarray
        x-values for the fitted curve.
    fit_curve : np.ndarray
        Best-fit lognormal PDF values.
    fit_error : np.ndarray
        ±3σ uncertainty band half-width at each x-grid point.
    unit : str
        Inherited unit string.
    label : str
        Inherited label string.
    """

    geometric_mean: float
    shape: float
    params_err: np.ndarray
    best_n_bins: int
    xgrid: np.ndarray
    fit_curve: np.ndarray
    fit_error: np.ndarray
    unit: str
    label: str


# ---------------------------------------------------------------------------
# Statistics results
# ---------------------------------------------------------------------------


@dataclass
class MeanResult:
    """Output of :func:`stamp.stats.amean` or :func:`stamp.stats.gmean`.

    Parameters
    ----------
    mean : float
        Arithmetic or geometric mean.
    std : float
        For arithmetic mean: Bessel-corrected standard deviation.
        For geometric mean: multiplicative standard deviation.
    ci_low : float
        Lower confidence interval bound.
    ci_high : float
        Upper confidence interval bound.
    ci_length : float
        ``ci_high - ci_low``.
    n : int
        Sample size.
    unit : str
        Inherited unit string.
    label : str
        Inherited label string.
    """

    mean: float
    std: float
    ci_low: float
    ci_high: float
    ci_length: float
    n: int
    unit: str
    label: str


@dataclass
class MedianResult:
    """Output of :func:`stamp.stats.median`.

    Parameters
    ----------
    median : float
        Sample median.
    iqr : float
        Interquartile range (Q75 − Q25).
    ci_low : float
        Lower confidence interval bound.
    ci_high : float
        Upper confidence interval bound.
    ci_length : float
        ``ci_high - ci_low``.
    n : int
        Sample size.
    unit : str
        Inherited unit string.
    label : str
        Inherited label string.
    """

    median: float
    iqr: float
    ci_low: float
    ci_high: float
    ci_length: float
    n: int
    unit: str
    label: str


@dataclass
class PeakResult:
    """Output of :func:`stamp.stats.freq_peak`.

    Parameters
    ----------
    peak : float
        Grain size at the KDE density maximum.
    peak_density : float
        Density value at the peak.
    xgrid : np.ndarray
        x-values used for KDE evaluation.
    density : np.ndarray
        KDE density values.
    bandwidth : float
        Resolved bandwidth value used.
    unit : str
        Inherited unit string.
    label : str
        Inherited label string.
    """

    peak: float
    peak_density: float
    xgrid: np.ndarray
    density: np.ndarray
    bandwidth: float
    unit: str
    label: str


@dataclass
class FitResult:
    """Output of :func:`stamp.stats.fit`.

    Parameters
    ----------
    distribution : str
        ``"normal"`` or ``"lognormal"``.
    params : dict
        MLE parameters.  Keys: ``loc``, ``scale`` for normal;
        ``s``, ``loc``, ``scale`` for lognormal.
    r_squared : float
        R² of fitted CDF vs empirical CDF.
    ks_statistic : float
        Kolmogorov–Smirnov D statistic.
    ks_pvalue : float
        KS p-value; large p indicates the distribution is not rejected.
    unit : str
        Inherited unit string.
    label : str
        Inherited label string.
    """

    distribution: str
    params: dict
    r_squared: float
    ks_statistic: float
    ks_pvalue: float
    unit: str
    label: str


@dataclass
class SimulationResult:
    """Output of :func:`stamp.simulate.simulate_section`.

    Parameters
    ----------
    true_diameters : MeasurementData
        Full pool of ``n_grains`` 3-D sphere diameters (ground truth).
    apparent_diameters : MeasurementData
        ``n_intersections`` 2-D circle diameters from random cross-sections.
    mu : float
        Input geometric mean (lognormal) or arithmetic mean (normal).
    sigma : float
        Input log-scale shape σ of ln D (lognormal) or standard deviation (normal).
    distribution : str
        ``"lognormal"`` or ``"normal"``.
    n_grains : int
        Size of the 3-D grain pool.
    n_intersections : int
        Number of 2-D section measurements generated.
    unit : str
        Physical unit string.
    seed : int or None
        Random seed used; ``None`` if not supplied.
    """

    true_diameters: MeasurementData
    apparent_diameters: MeasurementData
    mu: float
    sigma: float
    distribution: str
    n_grains: int
    n_intersections: int
    unit: str
    seed: int | None


@dataclass
class DescribeResult:
    """Output of :func:`stamp.stats.describe`.

    Parameters
    ----------
    n : int
        Sample size.
    amean : MeanResult
        Arithmetic mean (ASTM CI method).
    gmean : MeanResult
        Geometric mean (CLT CI method).
    median : MedianResult
        Median with Hollander–Wolfe CI.
    peak : PeakResult
        KDE mode (Silverman bandwidth).
    percentiles : dict
        Mapping of {5, 10, 25, 75, 90, 95} → value.
    unit : str
        Inherited unit string.
    label : str
        Inherited label string.
    """

    n: int
    amean: MeanResult
    gmean: MeanResult
    median: MedianResult
    peak: PeakResult
    percentiles: dict = field(default_factory=dict)
    unit: str = ""
    label: str = ""


def _coerce_to_measurement(
    data: MeasurementData | pd.DataFrame | pd.Series,
) -> MeasurementData:
    """Accept a single-column DataFrame or labelled Series; return MeasurementData.

    Allows all public stats / stereo / plot functions to consume the DataFrame
    returned by :func:`stamp.io.load` directly, without the caller needing to
    unwrap it manually.  A :class:`MeasurementData` is passed through unchanged.
    """
    if isinstance(data, MeasurementData):
        return data
    import pandas as _pd  # lazy import — pandas is a required dep but _types stays lean

    if isinstance(data, _pd.DataFrame):
        if data.shape[1] != 1:
            raise ValueError(
                f"DataFrame must have exactly one column, got {data.shape[1]}."
            )
        col = data.iloc[:, 0]
        return MeasurementData(
            values=col.to_numpy(dtype=np.float64),
            unit=data.attrs.get("unit", ""),
            label=data.attrs.get(
                "label", str(col.name) if col.name is not None else "Feature"
            ),
        )
    if isinstance(data, _pd.Series):
        return MeasurementData(
            values=data.to_numpy(dtype=np.float64),
            unit=data.attrs.get("unit", ""),
            label=data.attrs.get(
                "label", str(data.name) if data.name is not None else "Feature"
            ),
        )
    raise TypeError(
        f"Expected MeasurementData, DataFrame, or Series; got {type(data).__name__}."
    )
