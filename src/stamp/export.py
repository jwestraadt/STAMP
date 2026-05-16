from __future__ import annotations

import logging
import threading
import warnings
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties

if TYPE_CHECKING:
    from matplotlib.figure import Figure

# ── Preset definitions ────────────────────────────────────────────────────────

_PRESET_VALUES: dict[str, dict[str, object]] = {
    "default": {
        "font_family": "Arial",
        "font_size": 8.0,
        "tick_size": 7.0,
        "legend_size": 7.0,
        "panel_label_size": 8.0,
        "line_width": 1.0,
        "axis_line_width": 0.75,
        "tick_length": 3.0,
        "single_col_mm": 89.0,
        "one_half_col_mm": 120.0,
        "double_col_mm": 180.0,
        "dpi": 600,
        "bw": False,
    },
    "nature": {
        "font_family": "Arial",
        "font_size": 7.0,
        "tick_size": 6.0,
        "legend_size": 6.0,
        "panel_label_size": 8.0,
        "line_width": 0.75,
        "axis_line_width": 0.5,
        "tick_length": 2.5,
        "single_col_mm": 89.0,
        "one_half_col_mm": 120.0,
        "double_col_mm": 180.0,
        "dpi": 600,
        "bw": True,
    },
    "jama": {
        "font_family": "Arial",
        "font_size": 8.0,
        "tick_size": 7.0,
        "legend_size": 7.0,
        "panel_label_size": 8.0,
        "line_width": 0.75,
        "axis_line_width": 0.5,
        "tick_length": 3.0,
        "single_col_mm": 85.0,
        "one_half_col_mm": 114.0,
        "double_col_mm": 175.0,
        "dpi": 600,
        "bw": False,
    },
}

# Thread-local storage for the active style — lets stamp.plot read it without
# needing a global mutable reference.
_style_local: threading.local = threading.local()

_VECTOR_FMTS: frozenset[str] = frozenset({"pdf", "eps", "svg"})


def _active_bw() -> bool:
    """Return True if the current thread is inside a B&W journal_style context."""
    return bool(getattr(_style_local, "bw", False))


_VALID_FORMATS: frozenset[str] = frozenset({"pdf", "svg", "eps", "tiff", "png"})

# Ranked sans-serif fallback chain — metrically compatible Helvetica substitutes
# listed in preference order so matplotlib picks the best one available.
_FONT_FALLBACKS: list[str] = [
    "Helvetica",
    "Arial",
    "Nimbus Sans",
    "TeX Gyre Heros",
    "Liberation Sans",
    "DejaVu Sans",
]
_WIDTH_ATTR: dict[str, str] = {
    "single": "single_col_mm",
    "1.5": "one_half_col_mm",
    "double": "double_col_mm",
}

# Hatch cycle for B&W multi-series bar charts (no hatch for series 0 = single series)
_BW_HATCHES: tuple[str, ...] = ("", "////", "\\\\", "xxxx", "....", "oooo")


# ── JournalStyle ─────────────────────────────────────────────────────────────


@dataclass
class JournalStyle:
    """Journal typographic style configuration.

    Parameters
    ----------
    preset : str, optional
        Named preset to use as a base. Built-in options: ``"default"``,
        ``"nature"``, ``"jama"``.  Default is ``"default"``.
    font_family : str, optional
        Font family override (e.g. ``"Arial"``).  ``None`` uses the preset value.
    font_size : float, optional
        Axis label font size in pt.  ``None`` uses the preset value.
    tick_size : float, optional
        Tick label font size in pt.  ``None`` uses the preset value.
    legend_size : float, optional
        Legend font size in pt.  ``None`` uses the preset value.
    panel_label_size : float, optional
        Bold panel label font size in pt (used by :func:`panel_label`).
        ``None`` uses the preset value.
    line_width : float, optional
        Data line width in pt.  ``None`` uses the preset value.
    axis_line_width : float, optional
        Spine and axis line width in pt.  ``None`` uses the preset value.
    tick_length : float, optional
        Tick mark length in pt.  ``None`` uses the preset value.
    single_col_mm : float, optional
        Single-column figure width in mm.  ``None`` uses the preset value.
    one_half_col_mm : float, optional
        1.5-column figure width in mm.  ``None`` uses the preset value.
    double_col_mm : float, optional
        Double-column figure width in mm.  ``None`` uses the preset value.
    dpi : int, optional
        Raster output resolution.  ``None`` uses the preset value.

    Notes
    -----
    After construction all fields are guaranteed non-``None``; any field left as
    ``None`` is resolved from the preset.

    Raises
    ------
    ValueError
        If *preset* is not a recognised built-in name.

    Examples
    --------
    >>> style = JournalStyle(preset="nature", font_size=9)
    >>> style.font_size
    9
    >>> style.tick_size   # resolved from nature preset
    6.0
    """

    preset: str = "default"
    font_family: str | None = None
    font_size: float | None = None
    tick_size: float | None = None
    legend_size: float | None = None
    panel_label_size: float | None = None
    line_width: float | None = None
    axis_line_width: float | None = None
    tick_length: float | None = None
    single_col_mm: float | None = None
    one_half_col_mm: float | None = None
    double_col_mm: float | None = None
    dpi: int | None = None
    bw: bool | None = None

    def __post_init__(self) -> None:
        if self.preset not in _PRESET_VALUES:
            raise ValueError(
                f"Unknown preset {self.preset!r}. Available: {sorted(_PRESET_VALUES)}."
            )
        base = _PRESET_VALUES[self.preset]
        for field_name, preset_value in base.items():
            if getattr(self, field_name) is None:
                setattr(self, field_name, preset_value)


# ── Internal helpers ─────────────────────────────────────────────────────────


def _check_fonts(font_family: str, stacklevel: int = 3) -> None:
    """Warn once if the requested font is not available in matplotlib's font cache."""
    prop = FontProperties(family=font_family)
    found_path = font_manager.findfont(prop, fallback_to_default=True)
    found_name = font_manager.get_font(found_path).family_name
    if found_name.lower() != font_family.lower():
        warnings.warn(
            f"Font '{font_family}' not found in matplotlib font cache; "
            f"falling back to '{found_name}'. "
            f"Install fonts-urw-base35 (Linux) or Arial (Windows) to resolve this.",
            UserWarning,
            stacklevel=stacklevel,
        )


def _build_rc(style: JournalStyle) -> dict[str, object]:
    """Build the rcParams dict from a resolved JournalStyle."""
    return {
        "font.family": "sans-serif",
        "font.sans-serif": [style.font_family]
        + [f for f in _FONT_FALLBACKS if f != style.font_family],
        "axes.labelsize": style.font_size,
        "xtick.labelsize": style.tick_size,
        "ytick.labelsize": style.tick_size,
        "legend.fontsize": style.legend_size,
        "lines.linewidth": style.line_width,
        "axes.linewidth": style.axis_line_width,
        "xtick.major.size": style.tick_length,
        "ytick.major.size": style.tick_length,
        "xtick.major.width": style.axis_line_width,
        "ytick.major.width": style.axis_line_width,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "savefig.dpi": style.dpi,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }


# ── Style application ─────────────────────────────────────────────────────────


def apply_style(style: JournalStyle) -> None:
    """Apply journal-style rcParams globally (persistent, not scoped to a context).

    Prefer :func:`journal_style` for scoped styling so that rcParams are
    restored when the block exits.  Use ``apply_style`` at the top of a
    script where all subsequent figures should share the same conventions.

    Parameters
    ----------
    style : JournalStyle
        Resolved style configuration.

    Warns
    -----
    UserWarning
        If the requested font is not found in matplotlib's font cache.

    Notes
    -----
    Styling must be applied **before** creating any figures.  rcParams changes
    do not retroactively affect open figures.
    """
    _check_fonts(style.font_family, stacklevel=2)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    matplotlib.rcParams.update(_build_rc(style))
    _style_local.bw = bool(style.bw)


@contextmanager
def journal_style(style: JournalStyle) -> Iterator[None]:
    """Apply journal-style rcParams for the duration of a ``with`` block.

    Parameters
    ----------
    style : JournalStyle
        Resolved style object (from :class:`JournalStyle`).

    Yields
    ------
    None

    Warns
    -----
    UserWarning
        If the font specified by *style.font_family* is not found in
        matplotlib's font cache and a fallback will be used.

    Examples
    --------
    >>> from stamp.plot import distribution
    >>> style = JournalStyle(preset="nature")
    >>> with journal_style(style):
    ...     fig = distribution(data, figsize=(89/25.4, 89/25.4 * 0.75))
    """
    _check_fonts(style.font_family, stacklevel=3)
    _mpl_font_log = logging.getLogger("matplotlib.font_manager")
    _prev_level = _mpl_font_log.level
    _mpl_font_log.setLevel(logging.ERROR)
    previous_bw = getattr(_style_local, "bw", False)
    _style_local.bw = bool(style.bw)
    try:
        with matplotlib.rc_context(_build_rc(style)):
            yield
    finally:
        _style_local.bw = previous_bw
        _mpl_font_log.setLevel(_prev_level)


# ── Figure helper ─────────────────────────────────────────────────────────────


def figure_for(
    style: JournalStyle,
    *,
    width: Literal["single", "1.5", "double"] = "single",
    aspect: float = 0.75,
) -> Figure:
    """Create a blank :class:`~matplotlib.figure.Figure` sized to a journal column.

    Parameters
    ----------
    style : JournalStyle
        Style whose column-width values are used.
    width : {"single", "1.5", "double"}, optional
        Column width category.  Default ``"single"``.
    aspect : float, optional
        Height / width ratio.  Default ``0.75``.

    Returns
    -------
    matplotlib.figure.Figure
        Unstyled blank figure at the requested physical size.

    Raises
    ------
    ValueError
        If *width* is not one of the three recognised values.

    Examples
    --------
    >>> style = JournalStyle()
    >>> fig = figure_for(style, width="single", aspect=0.75)
    >>> round(fig.get_figwidth(), 2)
    3.5
    """
    if width not in _WIDTH_ATTR:
        raise ValueError(
            f"width must be one of {sorted(_WIDTH_ATTR)!r}, got {width!r}."
        )
    mm = getattr(style, _WIDTH_ATTR[width])
    w_in = mm / 25.4  # type: ignore[operator]
    return plt.figure(figsize=(w_in, w_in * aspect), layout="constrained")


# ── Panel label helper ────────────────────────────────────────────────────────


def panel_label(
    ax: plt.Axes,
    letter: str,
    spec: JournalStyle | None = None,
) -> None:
    """Place a bold panel label outside the axes, top-left corner.

    Positions the label at ``(-0.18, 1.02)`` in axes coordinates so it sits
    above and to the left of the plot area, following Nature/Science conventions.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    letter : str
        Label text, e.g. ``"a"``, ``"b"``.
    spec : JournalStyle, optional
        Style whose ``panel_label_size`` is used.  Defaults to 8 pt.

    Examples
    --------
    >>> fig, (ax1, ax2) = plt.subplots(1, 2)
    >>> panel_label(ax1, "a", NATURE)
    >>> panel_label(ax2, "b", NATURE)
    """
    size = spec.panel_label_size if spec is not None else 8.0
    ax.text(
        -0.18,
        1.02,
        letter,
        transform=ax.transAxes,
        fontsize=size,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


# ── B&W bar helper ────────────────────────────────────────────────────────────


def bw_bars(
    ax: plt.Axes,
    x: Sequence[float],
    height: Sequence[float],
    *,
    width: float = 0.8,
    series_idx: int = 0,
    label: str | None = None,
    **kwargs: object,
) -> None:
    """Draw a B&W-safe bar series using hatch patterns for multi-series plots.

    The first series (``series_idx=0``) has no hatch (solid white bars with
    black outlines).  Subsequent series cycle through ``_BW_HATCHES`` so that
    all series remain distinguishable after B&W printing or photocopying.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    x : sequence of float
        Bar centre positions.
    height : sequence of float
        Bar heights.
    width : float, optional
        Bar width.  Default ``0.8``.
    series_idx : int, optional
        Series index into the hatch cycle.  Default ``0`` (no hatch).
    label : str, optional
        Legend label for this series.
    **kwargs
        Forwarded to :func:`matplotlib.axes.Axes.bar`.

    Examples
    --------
    >>> bw_bars(ax, x=[1, 2, 3], height=[4, 5, 6], label="Series A")
    >>> bw_bars(ax, x=[1, 2, 3], height=[3, 4, 5], series_idx=1, label="Series B")
    """
    hatch = _BW_HATCHES[series_idx % len(_BW_HATCHES)]
    ax.bar(
        x,
        height,
        width=width,
        facecolor="white",
        edgecolor="black",
        hatch=hatch,
        label=label,
        **kwargs,
    )


# ── Save helper ───────────────────────────────────────────────────────────────


def save(
    fig: Figure,
    path: str | Path,
    formats: list[str] | None = None,
) -> list[Path]:
    """Save a figure to one or more file formats.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to save.
    path : str or Path
        Base output path **without** extension (e.g. ``"figures/fig1"``).
    formats : list of str, optional
        File formats to write.  Supported: ``"pdf"``, ``"svg"``, ``"eps"``,
        ``"tiff"``, ``"png"``.  Default ``["pdf"]``.

    Returns
    -------
    list of Path
        Paths of the files that were written.

    Raises
    ------
    ValueError
        If any entry in *formats* is not a supported format.
    ValueError
        If the parent directory of *path* does not exist.

    Examples
    --------
    >>> paths = save(fig, "figures/fig1", formats=["pdf", "tiff"])
    >>> [p.name for p in paths]
    ['fig1.pdf', 'fig1.tiff']
    """
    if formats is None:
        formats = ["pdf"]

    unsupported = [f for f in formats if f not in _VALID_FORMATS]
    if unsupported:
        raise ValueError(
            f"Unrecognised format(s) {unsupported!r}. "
            f"Supported: {sorted(_VALID_FORMATS)}."
        )

    parent = Path(path).parent
    if not parent.exists():
        raise ValueError(f"Output directory does not exist: {parent}")

    # For vector formats always embed fonts as Type 42 (TrueType), regardless of
    # whether journal_style() is active.  Type 3 fonts are rejected by Nature and
    # cannot survive Illustrator round-trips.
    written: list[Path] = []
    for fmt in formats:
        out = Path(str(path)).with_suffix(f".{fmt}")
        rc = {"pdf.fonttype": 42, "ps.fonttype": 42} if fmt in _VECTOR_FMTS else {}
        with matplotlib.rc_context(rc):
            fig.savefig(out, bbox_inches="tight")
        written.append(out)
    return written


# ── Table helpers ─────────────────────────────────────────────────────────────


def _apply_rounding(
    df: pd.DataFrame,
    decimals: int | dict[str, int],
) -> pd.DataFrame:
    out = df.copy()
    num_cols = out.select_dtypes("number").columns
    if isinstance(decimals, int):
        out[num_cols] = out[num_cols].round(decimals)
    else:
        for col, d in decimals.items():
            if col in out.columns:
                out[col] = out[col].round(d)
    return out


def _escape_latex_text(text: str) -> str:
    """Escape LaTeX special characters in a column header or unit string."""
    text = text.replace("µ", r"\textmu{}")
    text = text.replace("—", "---")  # Unicode em-dash → LaTeX ---
    text = text.replace("–", "--")  # Unicode en-dash  → LaTeX --
    # Escape % first, then upgrade the space + \% + space pattern to the
    # typographic thin-space variant — doing it this order avoids double-escaping
    # (replacing % then replacing \% would turn \% into \\%).
    text = text.replace("%", r"\%")
    text = text.replace(r" \% ", r"\,\% ")
    return text


def _format_cell(
    val: object,
    col: str,
    decimals: int | dict[str, int],
    *,
    siunitx: bool = False,
) -> str:
    if isinstance(val, float) and pd.isna(val):
        return "{---}" if siunitx else "---"
    if isinstance(val, float):
        d = decimals if isinstance(decimals, int) else decimals.get(col, 3)
        return f"{val:.{d}f}"
    return str(val)


def to_csv(
    df: pd.DataFrame,
    path: str | Path,
    *,
    decimals: int | dict[str, int] = 3,
) -> None:
    """Write a DataFrame to CSV with consistent numeric rounding.

    Parameters
    ----------
    df : pd.DataFrame
        Table to export.
    path : str or Path
        Output CSV path.
    decimals : int or dict of {str: int}, optional
        Decimal places — global integer or per-column mapping.  Default ``3``.

    Examples
    --------
    >>> to_csv(summary_df, "tables/table1.csv", decimals=2)
    """
    _apply_rounding(df, decimals).to_csv(path, index=False)


def to_latex(
    df: pd.DataFrame,
    path: str | Path | None = None,
    *,
    caption: str | None = None,
    label: str | None = None,
    decimals: int | dict[str, int] = 3,
    units: dict[str, str] | None = None,
    footnotes: dict[str, str] | None = None,
    row_notes: dict[str, str] | None = None,
    siunitx: bool = False,
) -> str:
    """Render a DataFrame as a LaTeX booktabs table.

    Produces a table with ``\\toprule``, ``\\midrule``, and ``\\bottomrule``
    (no ``\\hline``, no vertical rules).  Text columns are left-aligned;
    numeric columns are right-aligned by default, or decimal-aligned with
    siunitx ``S`` columns when *siunitx* is ``True``.

    Special characters in column headers are escaped automatically:
    ``µ`` → ``\\textmu{}``, ``—`` / ``–`` → ``---`` / ``--``,
    ``%`` → ``\\,\\%``.

    Footnotes are placed in a ``threeparttable`` / ``tablenotes`` block
    *outside* the ``tabular`` environment so they sit below ``\\bottomrule``
    at footnote size, following booktabs conventions.  Requires
    ``\\usepackage{threeparttable}`` in the document preamble.

    Parameters
    ----------
    df : pd.DataFrame
        Table to render.
    path : str or Path, optional
        If provided, writes the LaTeX string to this file.
    caption : str, optional
        Table caption for ``\\caption{}``.
    label : str, optional
        Table label for ``\\label{}``.
    decimals : int or dict of {str: int}, optional
        Decimal places — global or per-column.  Default ``3``.
    units : dict of {str: str}, optional
        Per-column units appended to the header, e.g. ``{"ECD": "µm"}``.
    footnotes : dict of {str: str}, optional
        Notes placed below the table via ``tablenotes``,
        e.g. ``{"a": "p < 0.05"}``.  Requires
        ``\\usepackage{threeparttable}`` in the preamble.
    row_notes : dict of {str: str}, optional
        Map from first-column cell values to footnote keys, used to place
        ``\\tnote{key}`` markers in the label column, e.g.
        ``{"Geometric mean": "a", "Median": "b"}``.  Only meaningful when
        *footnotes* is also supplied.
    siunitx : bool, optional
        If ``True``, numeric columns use the siunitx ``S`` column type for
        decimal alignment.  Requires ``\\usepackage{siunitx}`` in the preamble.
        Default ``False``.

    Returns
    -------
    str
        LaTeX source string.  Also written to *path* if provided.

    Examples
    --------
    >>> latex = to_latex(df, caption="Results.", label="tab:res",
    ...                  units={"Mean": "µm"}, decimals=2)
    >>> print(latex)
    """
    # Rename columns to include units, then escape header text
    col_map = {}
    if units:
        for col, unit in units.items():
            if col in df.columns:
                col_map[col] = f"{col} ({unit})"
    display_df = df.rename(columns=col_map) if col_map else df.copy()

    # Determine which display columns are numeric
    is_num: dict[str, bool] = {
        c: bool(pd.api.types.is_numeric_dtype(display_df[c]))
        for c in display_df.columns
    }

    # Build column format string
    if siunitx:
        d_global = decimals if isinstance(decimals, int) else 3
        col_fmts = []
        for c in display_df.columns:
            if is_num[c]:
                orig_col = next((k for k, v in col_map.items() if v == c), c)
                d = (
                    decimals
                    if isinstance(decimals, int)
                    else decimals.get(orig_col, d_global)
                )
                vals = display_df[c].dropna()
                int_digits = (
                    max(1, len(str(int(vals.abs().max())))) if not vals.empty else 1
                )
                col_fmts.append(f"S[table-format={int_digits}.{d}]")
            else:
                col_fmts.append("l")
        col_fmt = "".join(col_fmts)
    else:
        col_fmt = "".join("r" if is_num[c] else "l" for c in display_df.columns)

    # Build LaTeX manually (no jinja2 required)
    lines: list[str] = []
    if caption or label:
        lines.append(r"\begin{table}")
        lines.append(r"\centering")
        if caption:
            lines.append(rf"\caption{{{caption}}}")
        if label:
            lines.append(rf"\label{{{label}}}")

    if footnotes:
        lines.append(r"\begin{threeparttable}")

    lines.append(rf"\begin{{tabular}}{{{col_fmt}}}")
    lines.append(r"\toprule")

    # Header row — escape special chars; S columns need {braces} around text
    header_cells = []
    for c in display_df.columns:
        escaped = _escape_latex_text(str(c))
        header_cells.append(f"{{{escaped}}}" if (siunitx and is_num[c]) else escaped)
    lines.append(" & ".join(header_cells) + r" \\")
    lines.append(r"\midrule")

    # Data rows — use original df column names for decimals lookup
    orig_cols = list(df.columns)
    for _, row in df.iterrows():
        cells = []
        for i, c in enumerate(orig_cols):
            cell = _format_cell(
                row[c],
                c,
                decimals,
                siunitx=siunitx and is_num.get(col_map.get(c, c), False),
            )
            # Inject \tnote{} marker into the first (label) column
            if i == 0 and row_notes:
                key = row_notes.get(str(row[c]))
                if key:
                    cell = cell + rf"\tnote{{{key}}}"
            cells.append(cell)
        lines.append(" & ".join(cells) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    # Footnotes in tablenotes block (outside tabular, inside threeparttable)
    if footnotes:
        lines.append(r"\begin{tablenotes}[flushleft]")
        lines.append(r"\footnotesize")
        for k, v in footnotes.items():
            lines.append(rf"\item[{k}] {v}")
        lines.append(r"\end{tablenotes}")
        lines.append(r"\end{threeparttable}")

    if caption or label:
        lines.append(r"\end{table}")

    latex_str = "\n".join(lines) + "\n"

    if path is not None:
        Path(path).write_text(latex_str, encoding="utf-8")

    return latex_str


# ── Pre-built preset instances ────────────────────────────────────────────────
# Import directly: ``from stamp.export import NATURE``

DEFAULT = JournalStyle()
"""Default journal style preset (Arial 8 pt, 89 mm column, 600 dpi)."""

NATURE = JournalStyle(preset="nature")
"""Nature Publishing Group style (Arial 7 pt, 89 mm column, B&W)."""

JAMA = JournalStyle(preset="jama")
"""JAMA style (Arial 8 pt, 85 mm column, 600 dpi)."""
