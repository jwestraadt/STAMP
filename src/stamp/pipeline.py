"""Multi-state scripted analysis pipeline."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field as dc_field
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from stamp._types import DescribeResult, MeasurementData
from stamp.io import _ALL_EXTENSIONS, load
from stamp.plot import _C_TEXT, _apply_style
from stamp.stats import describe

_VALID_METRICS = {"amean", "gmean", "median"}
_METRIC_LABELS = {
    "amean": "Arithmetic mean",
    "gmean": "Geometric mean",
    "median": "Median",
}

_STATE_COLORS = [
    "#80419d",
    "#2F4858",
    "#e07b39",
    "#5c9e6e",
    "#fec44f",
    "#c62a47",
    "#0077b6",
    "#6d6875",
]


@dataclass
class FieldResult:
    """Results for a single field-of-view within a material state.

    Parameters
    ----------
    state : str
        Name of the parent material state.
    path : Path
        Source file path.
    data : MeasurementData
        Loaded measurement data.
    stats : DescribeResult
        Full descriptive statistics for this field.
    """

    state: str
    path: Path
    data: MeasurementData
    stats: DescribeResult


@dataclass
class StateResult:
    """Aggregated results for one material state.

    Parameters
    ----------
    name : str
        Material state label.
    fields : list of FieldResult
        One entry per field-of-view.
    """

    name: str
    fields: list[FieldResult] = dc_field(default_factory=list)


@dataclass
class PipelineResult:
    """Full output of :func:`run`.

    Parameters
    ----------
    states : list of StateResult
        Per-state results in the order they were supplied.
    summary : pd.DataFrame
        One row per field-of-view.  Columns: ``state``, ``fov``, ``file``,
        ``n``, ``unit``, ``amean``, ``amean_std``, ``amean_ci_low``,
        ``amean_ci_high``, ``gmean``, ``gmean_std``, ``gmean_ci_low``,
        ``gmean_ci_high``, ``median``, ``median_iqr``, ``median_ci_low``,
        ``median_ci_high``, ``peak``, ``p5``, ``p10``, ``p25``, ``p75``,
        ``p90``, ``p95``.
    """

    states: list[StateResult]
    summary: pd.DataFrame


def run(
    states: dict[str, Path | str | Sequence[Path | str]],
    column: str | int,
    unit: str,
    label: str | None = None,
    ci: float = 0.95,
    output_dir: Path | str | None = None,
    metric: str = "amean",
    dpi: int = 300,
    **load_kwargs,
) -> PipelineResult:
    """Run the full analysis pipeline on multiple material states.

    For each state, every field-of-view file is loaded, descriptive
    statistics are computed, and results are aggregated into a summary
    table and box-plot figure.

    Parameters
    ----------
    states : dict
        Mapping of state name to source files.  Each value may be:

        * a :class:`~pathlib.Path` or ``str`` pointing to a **directory**
          (all supported files in the directory are used as fields-of-view),
        * a :class:`~pathlib.Path` or ``str`` pointing to a single file, or
        * a sequence of file paths.

    column : str or int
        Column name or 0-based index passed to :func:`stamp.io.load`.
    unit : str
        Physical unit string, e.g. ``"µm"``.
    label : str, optional
        Display label for the measured feature.
    ci : float, optional
        Confidence level for all statistics.  Default 0.95.
    output_dir : Path or str, optional
        If given, writes ``pipeline_summary.csv`` and
        ``boxplot_<metric>.png`` to this directory automatically.
    metric : str, optional
        Statistic used for the auto-saved box plot: ``"amean"``,
        ``"gmean"``, or ``"median"``.  Default ``"amean"``.
    dpi : int, optional
        Figure resolution when *output_dir* is set.  Default 300.
    **load_kwargs
        Additional keyword arguments forwarded to :func:`stamp.io.load`
        (e.g. ``delimiter``, ``skip_rows``, ``sheet_name``).

    Returns
    -------
    PipelineResult
        Container holding per-state results and a summary DataFrame.

    Raises
    ------
    ValueError
        If *metric* is unknown, or no files are found for a state.
    FileNotFoundError
        If a supplied path does not exist.

    Examples
    --------
    >>> result = run(
    ...     states={
    ...         "As-received": "data/as_received/",
    ...         "Annealed 800 C": ["data/ann800_fov1.csv", "data/ann800_fov2.csv"],
    ...     },
    ...     column="ECD_um",
    ...     unit="µm",
    ...     output_dir="results/",
    ... )
    >>> result.summary.head()
    """
    if metric not in _VALID_METRICS:
        raise ValueError(
            f"metric must be one of {sorted(_VALID_METRICS)}, got {metric!r}."
        )

    state_results: list[StateResult] = []
    rows: list[dict] = []

    for state_name, source in states.items():
        files = _resolve_files(source)
        if not files:
            raise ValueError(f"No supported files found for state {state_name!r}.")

        sr = StateResult(name=state_name)
        for fp in files:
            data = load(fp, column=column, unit=unit, label=label, **load_kwargs)
            stats = describe(data, ci=ci)
            fr = FieldResult(state=state_name, path=fp, data=data, stats=stats)
            sr.fields.append(fr)
            rows.append(_field_to_row(fr))
        state_results.append(sr)

    summary = pd.DataFrame(rows)
    result = PipelineResult(states=state_results, summary=summary)

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        export_csv(result, out / "pipeline_summary.csv")
        fig = boxplot(result, metric=metric, dpi=dpi)
        fig.savefig(out / f"boxplot_{metric}.png", dpi=dpi, bbox_inches="tight")
        plt.close(fig)

    return result


def boxplot(
    result: PipelineResult,
    metric: str = "amean",
    output_path: Path | str | None = None,
    dpi: int = 300,
    figsize: tuple[float, float] | None = None,
) -> Figure:
    """Side-by-side box plot comparing per-FOV statistics across material states.

    Each box represents one material state.  The box spans the
    interquartile range of the per-field-of-view metric values; individual
    data points are overlaid as a jittered strip plot.

    Parameters
    ----------
    result : PipelineResult
        Output of :func:`run`.
    metric : str, optional
        Statistic to plot: ``"amean"``, ``"gmean"``, or ``"median"``.
        Default ``"amean"``.
    output_path : Path or str, optional
        If given, the figure is saved to this path.
    dpi : int, optional
        Output resolution.  Default 300.
    figsize : tuple of float, optional
        Figure size in inches.  Defaults to
        ``(max(6.4, n_states * 1.8), 4.8)``.

    Returns
    -------
    matplotlib.figure.Figure

    Raises
    ------
    ValueError
        If *metric* is not ``"amean"``, ``"gmean"``, or ``"median"``.
    """
    if metric not in _VALID_METRICS:
        raise ValueError(
            f"metric must be one of {sorted(_VALID_METRICS)}, got {metric!r}."
        )

    n_states = len(result.states)
    if figsize is None:
        figsize = (max(6.4, n_states * 1.8), 4.8)

    fig, ax = plt.subplots(figsize=figsize)
    positions = list(range(1, n_states + 1))
    rng = np.random.default_rng(42)

    for i, sr in enumerate(result.states):
        values = [_get_metric(fr.stats, metric) for fr in sr.fields]
        color = _STATE_COLORS[i % len(_STATE_COLORS)]
        ax.boxplot(
            values,
            positions=[positions[i]],
            widths=0.5,
            patch_artist=True,
            boxprops=dict(facecolor=color, alpha=0.4, linewidth=1.2),
            medianprops=dict(color=_C_TEXT, linewidth=1.5),
            whiskerprops=dict(color=_C_TEXT, linewidth=1.0),
            capprops=dict(color=_C_TEXT, linewidth=1.0),
            flierprops=dict(marker="o", markerfacecolor=color, markersize=5, alpha=0.6),
            manage_ticks=False,
        )
        jitter = rng.uniform(-0.08, 0.08, len(values))
        ax.scatter(
            [positions[i] + j for j in jitter],
            values,
            color=color,
            alpha=0.85,
            s=35,
            zorder=3,
        )

    ax.set_xticks(positions)
    ax.set_xticklabels([sr.name for sr in result.states], rotation=20, ha="right")

    unit = result.states[0].fields[0].data.unit if result.states else ""
    feat_label = result.states[0].fields[0].data.label if result.states else ""
    ax.set_ylabel(f"{_METRIC_LABELS[metric]} — {feat_label} ({unit})", color=_C_TEXT)
    ax.set_title(
        f"{_METRIC_LABELS[metric]} per field-of-view by material state",
        color=_C_TEXT,
    )
    _apply_style(ax)
    fig.tight_layout()

    if output_path is not None:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

    return fig


def export_csv(result: PipelineResult, output_path: Path | str) -> None:
    """Write the pipeline summary table to a CSV file.

    Parameters
    ----------
    result : PipelineResult
        Output of :func:`run`.
    output_path : Path or str
        Destination file path.

    Examples
    --------
    >>> export_csv(result, "results/summary.csv")
    """
    result.summary.to_csv(output_path, index=False)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_files(source: Path | str | Sequence[Path | str]) -> list[Path]:
    """Resolve a state source to an ordered list of file paths."""
    if isinstance(source, (str, Path)):
        p = Path(source)
        if p.is_dir():
            return sorted(
                f
                for f in p.iterdir()
                if f.is_file() and f.suffix.lower() in _ALL_EXTENSIONS
            )
        return [p]
    return [Path(f) for f in source]


def _get_metric(stats: DescribeResult, metric: str) -> float:
    """Extract the scalar value for *metric* from a DescribeResult."""
    if metric == "amean":
        return stats.amean.mean
    if metric == "gmean":
        return stats.gmean.mean
    return stats.median.median


def _field_to_row(fr: FieldResult) -> dict:
    """Flatten a FieldResult to a summary dict."""
    s = fr.stats
    return {
        "state": fr.state,
        "fov": fr.path.stem,
        "file": str(fr.path),
        "n": s.n,
        "unit": fr.data.unit,
        "amean": s.amean.mean,
        "amean_std": s.amean.std,
        "amean_ci_low": s.amean.ci_low,
        "amean_ci_high": s.amean.ci_high,
        "gmean": s.gmean.mean,
        "gmean_std": s.gmean.std,
        "gmean_ci_low": s.gmean.ci_low,
        "gmean_ci_high": s.gmean.ci_high,
        "median": s.median.median,
        "median_iqr": s.median.iqr,
        "median_ci_low": s.median.ci_low,
        "median_ci_high": s.median.ci_high,
        "peak": s.peak.peak,
        "p5": s.percentiles.get(5),
        "p10": s.percentiles.get(10),
        "p25": s.percentiles.get(25),
        "p75": s.percentiles.get(75),
        "p90": s.percentiles.get(90),
        "p95": s.percentiles.get(95),
    }
