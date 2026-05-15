"""Publication-ready figures for microstructural analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from scipy import stats as scipy_stats
from scipy.stats import gaussian_kde

from stamp._types import (
    FitResult,
    MeasurementData,
    SaltykovResult,
    SimulationResult,
    TwoStepResult,
    _coerce_to_measurement,
)

# ---------------------------------------------------------------------------
# Colour palette (GrainSizeTools-compatible)
# ---------------------------------------------------------------------------
_C_HIST = "#80419d"
_C_EDGE = "#C59fd7"
_C_LINE = "#2F4858"
_C_GMEAN = "#fec44f"
_C_FILL = "#80419d"
_C_TEXT = "#252525"

_VALID_PLOT = {"hist", "kde"}
_VALID_AVG = {"amean", "gmean", "median", "mode"}
_VALID_DIST = {"normal", "lognormal"}


def _apply_style(ax: plt.Axes) -> None:
    """Remove top/right spines and set text colour."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for item in (
        [ax.title, ax.xaxis.label, ax.yaxis.label]
        + ax.get_xticklabels()
        + ax.get_yticklabels()
    ):
        item.set_color(_C_TEXT)


def _save(fig: Figure, output_path: str | Path | None, dpi: int) -> None:
    if output_path is not None:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")


def distribution(
    data: MeasurementData,
    plot: tuple[str, ...] = ("hist", "kde"),
    avg: tuple[str, ...] = ("amean", "gmean", "median", "mode"),
    bins: int | str = "auto",
    bandwidth: str | float = "silverman",
    fit: FitResult | None = None,
    output_path: str | Path | None = None,
    dpi: int = 300,
    figsize: tuple[float, float] = (6.4, 4.8),
    **kwargs,
) -> Figure:
    """Histogram and/or KDE of the 2-D measurement distribution.

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Input measurements.  A single-column :class:`~pandas.DataFrame`
        returned by :func:`stamp.io.load` is accepted directly.
    plot : tuple of str, optional
        Elements to draw; subset of ``{"hist", "kde"}``.
    avg : tuple of str, optional
        Averages to annotate; subset of ``{"amean", "gmean", "median", "mode"}``.
    bins : int or str, optional
        Bin count or numpy strategy.  Default ``"auto"``.
    bandwidth : str or float, optional
        KDE bandwidth method.  Default ``"silverman"``.
    fit : FitResult, optional
        If provided, overlays the fitted PDF.
    output_path : str or Path, optional
        Save path; format inferred from extension.
    dpi : int, optional
        Output resolution.  Default 300.
    figsize : tuple of float, optional
        Figure size in inches.  Default ``(6.4, 4.8)``.

    Returns
    -------
    matplotlib.figure.Figure

    Raises
    ------
    ValueError
        If *plot* or *avg* contain unknown element names.
    """
    invalid_plot = set(plot) - _VALID_PLOT
    if invalid_plot:
        raise ValueError(
            f"Unknown plot element(s): {invalid_plot}. Valid: {_VALID_PLOT}"
        )
    invalid_avg = set(avg) - _VALID_AVG
    if invalid_avg:
        raise ValueError(f"Unknown avg element(s): {invalid_avg}. Valid: {_VALID_AVG}")

    data = _coerce_to_measurement(data)
    v = data.values
    fig, ax = plt.subplots(figsize=figsize)

    if "hist" in plot:
        ax.hist(
            v,
            bins=bins,
            density=True,
            color=_C_HIST,
            edgecolor=_C_EDGE,
            alpha=0.7,
            label="Data",
        )

    if "kde" in plot:
        bw = bandwidth if isinstance(bandwidth, str) else float(bandwidth)
        kde = gaussian_kde(v, bw_method=bw)
        xgrid = np.linspace(v.min(), v.max(), 512)
        density = kde(xgrid)
        ax.plot(xgrid, density, color=_C_LINE, lw=1.5, label="KDE")
        ax.fill_between(xgrid, density, alpha=0.2, color=_C_FILL)

    if fit is not None:
        xgrid = np.linspace(v.min(), v.max(), 512)
        if fit.distribution == "normal":
            pdf = scipy_stats.norm.pdf(xgrid, **fit.params)
        else:
            pdf = scipy_stats.lognorm.pdf(xgrid, **fit.params)
        ax.plot(
            xgrid,
            pdf,
            color=_C_GMEAN,
            lw=1.5,
            ls="--",
            label=f"Fit ({fit.distribution})",
        )

    # Annotate averages as vertical lines
    avg_vals = _compute_avg(v, avg, bandwidth)
    colours = {
        "amean": _C_LINE,
        "gmean": _C_GMEAN,
        "median": "#e07b39",
        "mode": "#5c9e6e",
    }
    for key, val in avg_vals.items():
        ax.axvline(val, color=colours[key], lw=1.2, ls="--", label=key)

    ax.set_xlabel(f"{data.label} ({data.unit})", color=_C_TEXT)
    ax.set_ylabel("Density", color=_C_TEXT)
    ax.set_title(data.label, color=_C_TEXT)
    ax.legend(fontsize=10)
    _apply_style(ax)
    fig.tight_layout()
    _save(fig, output_path, dpi)
    return fig


def saltykov_plot(
    result: SaltykovResult,
    output_path: str | Path | None = None,
    dpi: int = 300,
    figsize: tuple[float, float] = (10.0, 4.8),
    **kwargs,
) -> Figure:
    """Dual-panel figure from a :class:`SaltykovResult`.

    Left panel: bar histogram of 3-D grain frequencies.
    Right panel: volume-weighted cumulative distribution.

    Parameters
    ----------
    result : SaltykovResult
        Output of :func:`stamp.stereo.saltykov`.
    output_path : str or Path, optional
        Save path.
    dpi : int, optional
        Output resolution.  Default 300.
    figsize : tuple of float, optional
        Figure size in inches.  Default ``(10, 4.8)``.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Left: 3D frequency histogram
    ax1.bar(
        result.bin_midpoints,
        result.freq3d,
        width=result.bin_width * 0.9,
        color=_C_HIST,
        edgecolor=_C_EDGE,
        alpha=0.8,
    )
    ax1.set_xlabel(f"{result.label} ({result.unit})", color=_C_TEXT)
    ax1.set_ylabel("Frequency density", color=_C_TEXT)
    ax1.set_title("3-D grain size distribution", color=_C_TEXT)
    _apply_style(ax1)

    # Right: volume-weighted CDF
    ax2.plot(result.bin_midpoints, result.cdf_vol, color=_C_LINE, lw=1.5)
    ax2.scatter(result.bin_midpoints, result.cdf_vol, color=_C_LINE, s=20, zorder=5)
    ax2.set_xlabel(f"{result.label} ({result.unit})", color=_C_TEXT)
    ax2.set_ylabel("Cumulative volume fraction (%)", color=_C_TEXT)
    ax2.set_title("Volume-weighted CDF", color=_C_TEXT)
    _apply_style(ax2)

    fig.tight_layout()
    _save(fig, output_path, dpi)
    return fig


def twostep_plot(
    result: TwoStepResult,
    output_path: str | Path | None = None,
    dpi: int = 300,
    figsize: tuple[float, float] = (6.4, 4.8),
    **kwargs,
) -> Figure:
    """Single-panel figure from a :class:`TwoStepResult`.

    Shows the best Saltykov histogram with overlaid lognormal best-fit
    curve and ±3σ uncertainty band.

    Parameters
    ----------
    result : TwoStepResult
        Output of :func:`stamp.stereo.two_step`.
    output_path : str or Path, optional
        Save path.
    dpi : int, optional
        Output resolution.  Default 300.
    figsize : tuple of float, optional
        Figure size in inches.  Default ``(6.4, 4.8)``.

    Returns
    -------
    matplotlib.figure.Figure
    """

    fig, ax = plt.subplots(figsize=figsize)

    # Reconstruct the best Saltykov result to get bin width for bar width
    ax.plot(
        result.xgrid,
        result.fit_curve,
        color=_C_LINE,
        lw=1.5,
        label="Best-fit lognormal",
    )
    ax.fill_between(
        result.xgrid,
        result.fit_curve - result.fit_error,
        result.fit_curve + result.fit_error,
        alpha=0.25,
        color=_C_LINE,
        label="±3σ uncertainty",
    )

    ax.set_xlabel(f"{result.label} ({result.unit})", color=_C_TEXT)
    ax.set_ylabel("Frequency density", color=_C_TEXT)
    ax.set_title("Two-step lognormal fit", color=_C_TEXT)
    ax.legend(fontsize=10)
    _apply_style(ax)
    fig.tight_layout()
    _save(fig, output_path, dpi)
    return fig


def distribution_profile(
    data: MeasurementData,
    kind: str = "pdf",
    fit: FitResult | None = None,
    output_path: str | Path | None = None,
    dpi: int = 300,
    figsize: tuple[float, float] = (6.4, 4.8),
    **kwargs,
) -> Figure:
    """PDF or CDF profile with optional fitted distribution overlay.

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Input measurements.  A single-column :class:`~pandas.DataFrame`
        returned by :func:`stamp.io.load` is accepted directly.
    kind : str, optional
        ``"pdf"`` (kernel density) or ``"cdf"`` (empirical).  Default ``"pdf"``.
    fit : FitResult, optional
        Overlays the fitted parametric curve.
    output_path : str or Path, optional
        Save path.
    dpi : int, optional
        Output resolution.  Default 300.
    figsize : tuple of float, optional
        Figure size in inches.  Default ``(6.4, 4.8)``.

    Returns
    -------
    matplotlib.figure.Figure

    Raises
    ------
    ValueError
        If *kind* is not ``"pdf"`` or ``"cdf"``.
    """
    if kind not in ("pdf", "cdf"):
        raise ValueError(f"kind must be 'pdf' or 'cdf', got {kind!r}.")

    data = _coerce_to_measurement(data)
    v = data.values
    fig, ax = plt.subplots(figsize=figsize)

    xgrid = np.linspace(v.min(), v.max(), 512)

    if kind == "pdf":
        kde = gaussian_kde(v, bw_method="silverman")
        profile = kde(xgrid)
        ax.plot(xgrid, profile, color=_C_LINE, lw=1.5, label="KDE PDF")
        ax.fill_between(xgrid, profile, alpha=0.25, color=_C_FILL)
        ax.set_ylabel("Density", color=_C_TEXT)
    else:
        sorted_v = np.sort(v)
        cdf = np.arange(1, len(v) + 1) / len(v)
        ax.plot(sorted_v, cdf, color=_C_LINE, lw=1.5, label="Empirical CDF")
        ax.set_ylabel("Cumulative probability", color=_C_TEXT)

    if fit is not None:
        if fit.distribution == "normal":
            dist_obj = scipy_stats.norm(**fit.params)
        else:
            dist_obj = scipy_stats.lognorm(**fit.params)

        if kind == "pdf":
            ax.plot(
                xgrid,
                dist_obj.pdf(xgrid),
                color=_C_GMEAN,
                lw=1.5,
                ls="--",
                label=f"Fit ({fit.distribution})",
            )
        else:
            ax.plot(
                xgrid,
                dist_obj.cdf(xgrid),
                color=_C_GMEAN,
                lw=1.5,
                ls="--",
                label=f"Fit ({fit.distribution})",
            )

    ax.set_xlabel(f"{data.label} ({data.unit})", color=_C_TEXT)
    ax.set_title(f"{data.label} — {kind.upper()}", color=_C_TEXT)
    ax.legend(fontsize=10)
    _apply_style(ax)
    fig.tight_layout()
    _save(fig, output_path, dpi)
    return fig


def qq_plot(
    data: MeasurementData,
    distribution: str = "lognormal",
    percent: float = 2.0,
    output_path: str | Path | None = None,
    dpi: int = 300,
    figsize: tuple[float, float] = (6.4, 4.8),
    **kwargs,
) -> Figure:
    """Quantile-quantile plot against a theoretical distribution.

    Parameters
    ----------
    data : MeasurementData, pd.DataFrame, or pd.Series
        Input measurements.  A single-column :class:`~pandas.DataFrame`
        returned by :func:`stamp.io.load` is accepted directly.
    distribution : str, optional
        ``"normal"`` or ``"lognormal"``.  Default ``"lognormal"``.
    percent : float, optional
        Percentile trim applied to each tail before plotting.  Default 2.
    output_path : str or Path, optional
        Save path.
    dpi : int, optional
        Output resolution.  Default 300.
    figsize : tuple of float, optional
        Figure size in inches.  Default ``(6.4, 4.8)``.

    Returns
    -------
    matplotlib.figure.Figure

    Raises
    ------
    ValueError
        If *distribution* is not ``"normal"`` or ``"lognormal"``.
    """
    if distribution not in _VALID_DIST:
        raise ValueError(
            f"distribution must be one of {_VALID_DIST}, got {distribution!r}."
        )

    data = _coerce_to_measurement(data)
    v = data.values
    lo_cut = np.percentile(v, percent)
    hi_cut = np.percentile(v, 100 - percent)
    v_trimmed = v[(v >= lo_cut) & (v <= hi_cut)]

    if distribution == "lognormal":
        transformed = np.log(v_trimmed)
        dist_obj = scipy_stats.norm
        xlabel = f"Theoretical quantiles (ln {data.label})"
        ylabel = f"Sample quantiles (ln {data.label})"
    else:
        transformed = v_trimmed
        dist_obj = scipy_stats.norm
        xlabel = f"Theoretical quantiles ({data.label})"
        ylabel = f"Sample quantiles ({data.label})"

    fig, ax = plt.subplots(figsize=figsize)
    (osm, osr), (slope, intercept, _) = scipy_stats.probplot(transformed, dist=dist_obj)
    ax.scatter(osm, osr, color=_C_HIST, edgecolors=_C_EDGE, alpha=0.7, s=20)
    fit_line = np.array([osm[0], osm[-1]]) * slope + intercept
    ax.plot([osm[0], osm[-1]], fit_line, color=_C_LINE, lw=1.5, label="Reference line")

    ax.set_xlabel(xlabel, color=_C_TEXT)
    ax.set_ylabel(ylabel, color=_C_TEXT)
    ax.set_title(f"Q-Q plot — {distribution}", color=_C_TEXT)
    ax.legend(fontsize=10)
    _apply_style(ax)
    fig.tight_layout()
    _save(fig, output_path, dpi)
    return fig


def comparison_plot(
    sim_result: SimulationResult,
    corrected: SaltykovResult | TwoStepResult,
    output_path: str | Path | None = None,
    dpi: int = 300,
    figsize: tuple[float, float] = (12.0, 4.8),
    **kwargs,
) -> Figure:
    """Two-panel validation figure comparing true 3-D vs stereologically corrected.

    Left panel: histogram + KDE of the 2-D apparent diameters, annotated with
    the apparent geometric mean.

    Right panel: KDE of the true 3-D diameters (filled) overlaid with the
    Saltykov bar histogram or two-step lognormal curve.  Both geometric means
    are annotated along with the percentage recovery error.

    Parameters
    ----------
    sim_result : SimulationResult
        Output of :func:`stamp.simulate.simulate_section`.
    corrected : SaltykovResult or TwoStepResult
        Output of :func:`stamp.stereo.saltykov` or :func:`stamp.stereo.two_step`.
    output_path : str or Path, optional
        Save path; format inferred from extension.
    dpi : int, optional
        Output resolution.  Default 300.
    figsize : tuple of float, optional
        Figure size in inches.  Default ``(12, 4.8)``.

    Returns
    -------
    matplotlib.figure.Figure

    Raises
    ------
    TypeError
        If *corrected* is not a :class:`SaltykovResult` or
        :class:`TwoStepResult`.
    """
    if not isinstance(corrected, (SaltykovResult, TwoStepResult)):
        raise TypeError(
            f"corrected must be a SaltykovResult or TwoStepResult, "
            f"got {type(corrected).__name__!r}."
        )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # ── Left panel: 2-D apparent distribution ────────────────────────────────
    v2d = sim_result.apparent_diameters.values
    ax1.hist(
        v2d,
        bins="auto",
        density=True,
        color=_C_HIST,
        edgecolor=_C_EDGE,
        alpha=0.7,
    )
    kde2d = gaussian_kde(v2d, bw_method="silverman")
    xg2d = np.linspace(v2d.min(), v2d.max(), 512)
    ax1.plot(xg2d, kde2d(xg2d), color=_C_LINE, lw=1.5)
    gmean_2d = float(np.exp(np.mean(np.log(v2d))))
    ax1.axvline(
        gmean_2d,
        color=_C_GMEAN,
        lw=1.5,
        ls="--",
        label=f"Geom. mean = {gmean_2d:.1f} {sim_result.unit}",
    )
    ax1.set_xlabel(
        f"{sim_result.apparent_diameters.label} ({sim_result.unit})",
        color=_C_TEXT,
    )
    ax1.set_ylabel("Density", color=_C_TEXT)
    ax1.set_title(
        f"2D apparent distribution  (n = {sim_result.n_intersections:,})",
        color=_C_TEXT,
    )
    ax1.legend(fontsize=9)
    _apply_style(ax1)

    # ── Right panel: true 3-D vs corrected ───────────────────────────────────
    v3d = sim_result.true_diameters.values
    gmean_true = float(np.exp(np.mean(np.log(v3d))))

    kde3d = gaussian_kde(v3d, bw_method="silverman")
    xg3d = np.linspace(v3d.min(), v3d.max(), 512)
    ax2.fill_between(xg3d, kde3d(xg3d), alpha=0.25, color=_C_HIST)
    ax2.plot(
        xg3d,
        kde3d(xg3d),
        color=_C_HIST,
        lw=1.5,
        label=f"True 3D  (n = {sim_result.n_grains:,})",
    )
    ax2.axvline(
        gmean_true,
        color=_C_HIST,
        lw=1.5,
        ls="--",
        label=f"True geom. mean = {gmean_true:.1f} {sim_result.unit}",
    )

    if isinstance(corrected, SaltykovResult):
        ax2.bar(
            corrected.bin_midpoints,
            corrected.freq3d,
            width=corrected.bin_width * 0.8,
            color=_C_LINE,
            edgecolor="white",
            alpha=0.65,
            label="Saltykov corrected",
        )
        w = corrected.freq3d * corrected.bin_width
        w_sum = w.sum()
        gmean_corrected = float(
            np.exp(np.dot(w, np.log(corrected.bin_midpoints)) / w_sum)
            if w_sum > 0
            else corrected.bin_midpoints.mean()
        )
        method_label = "Saltykov"
    else:  # TwoStepResult
        ax2.plot(
            corrected.xgrid,
            corrected.fit_curve,
            color=_C_LINE,
            lw=2.0,
            label="Two-step fit",
        )
        ax2.fill_between(
            corrected.xgrid,
            corrected.fit_curve - corrected.fit_error,
            corrected.fit_curve + corrected.fit_error,
            alpha=0.2,
            color=_C_LINE,
        )
        gmean_corrected = corrected.geometric_mean
        method_label = "Two-step"

    ax2.axvline(
        gmean_corrected,
        color=_C_LINE,
        lw=1.5,
        ls="--",
        label=f"Corrected geom. mean = {gmean_corrected:.1f} {sim_result.unit}",
    )
    recovery_err = abs(gmean_corrected - gmean_true) / gmean_true * 100
    ax2.set_title(
        f"True 3D vs {method_label} corrected — recovery error: {recovery_err:.1f}%",
        color=_C_TEXT,
    )
    ax2.set_xlabel(
        f"{sim_result.true_diameters.label} ({sim_result.unit})",
        color=_C_TEXT,
    )
    ax2.set_ylabel("Density", color=_C_TEXT)
    ax2.legend(fontsize=9)
    _apply_style(ax2)

    fig.tight_layout()
    _save(fig, output_path, dpi)
    return fig


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _compute_avg(
    v: np.ndarray,
    avg: tuple[str, ...],
    bandwidth: str | float,
) -> dict[str, float]:
    result = {}
    if "amean" in avg:
        result["amean"] = float(np.mean(v))
    if "gmean" in avg:
        result["gmean"] = float(np.exp(np.mean(np.log(v))))
    if "median" in avg:
        result["median"] = float(np.median(v))
    if "mode" in avg:
        bw = bandwidth if isinstance(bandwidth, str) else float(bandwidth)
        kde = gaussian_kde(v, bw_method=bw)
        xgrid = np.linspace(v.min(), v.max(), 512)
        result["mode"] = float(xgrid[np.argmax(kde(xgrid))])
    return result
