# Spec: `stamp.export` — Journal-style figure and table export

> **Status:** draft
> **Author:** Johan Westraadt
> **Branch:** `feat/export-journal-style`

---

## One-line summary

Apply publication-ready journal formatting to STAMP figures and export results tables as CSV or LaTeX (`stamp.export`).

---

## Public API

```python
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import matplotlib.figure
import pandas as pd


@dataclass
class JournalStyle:
    preset: str = "default"
    # Typography overrides (None → use preset value)
    font_family: str | None = None
    font_size: float | None = None        # axis label size (pt)
    tick_size: float | None = None        # tick label size (pt)
    legend_size: float | None = None      # legend font size (pt)
    # Geometry overrides
    line_width: float | None = None       # data line width (pt)
    axis_line_width: float | None = None  # spine / axis line width (pt)
    tick_length: float | None = None      # tick mark length (pt)
    # Figure sizing overrides (mm)
    single_col_mm: float | None = None
    one_half_col_mm: float | None = None
    double_col_mm: float | None = None
    # Output
    dpi: int | None = None                # raster output resolution


@contextmanager
def journal_style(style: JournalStyle) -> Iterator[None]:
    """Context manager — applies journal rcParams for the duration of the block."""
    ...


def figure_for(
    style: JournalStyle,
    *,
    width: Literal["single", "1.5", "double"] = "single",
    aspect: float = 0.75,
) -> matplotlib.figure.Figure:
    """Create a blank Figure sized to journal column width."""
    ...


def save(
    fig: matplotlib.figure.Figure,
    path: str | Path,
    formats: list[str] | None = None,
) -> list[Path]:
    """Save a figure to one or more formats. Returns the list of written paths."""
    ...


def to_csv(
    df: pd.DataFrame,
    path: str | Path,
    *,
    decimals: int | dict[str, int] = 3,
) -> None:
    """Write a DataFrame to a CSV file with consistent rounding."""
    ...


def to_latex(
    df: pd.DataFrame,
    path: str | Path | None = None,
    *,
    caption: str | None = None,
    label: str | None = None,
    decimals: int | dict[str, int] = 3,
    units: dict[str, str] | None = None,
    footnotes: dict[str, str] | None = None,
) -> str:
    """Render a DataFrame as a LaTeX booktabs table. Writes to path if given."""
    ...
```

### Parameters

#### `JournalStyle`

| Name | Type | Default | Description |
|---|---|---|---|
| `preset` | `str` | `"default"` | Named preset. Built-in: `"default"`, `"nature"`. |
| `font_family` | `str \| None` | `None` | Override font family (e.g. `"Arial"`). |
| `font_size` | `float \| None` | `None` | Axis label font size in pt. |
| `tick_size` | `float \| None` | `None` | Tick label font size in pt. |
| `legend_size` | `float \| None` | `None` | Legend font size in pt. |
| `line_width` | `float \| None` | `None` | Data line width in pt. |
| `axis_line_width` | `float \| None` | `None` | Spine and axis line width in pt. |
| `tick_length` | `float \| None` | `None` | Tick mark length in pt. |
| `single_col_mm` | `float \| None` | `None` | Single-column figure width in mm. |
| `one_half_col_mm` | `float \| None` | `None` | 1.5-column figure width in mm. |
| `double_col_mm` | `float \| None` | `None` | Double-column figure width in mm. |
| `dpi` | `int \| None` | `None` | Raster output resolution. |

#### `figure_for()`

| Name | Type | Default | Description |
|---|---|---|---|
| `style` | `JournalStyle` | — | Style to derive dimensions from. |
| `width` | `"single" \| "1.5" \| "double"` | `"single"` | Column width category. |
| `aspect` | `float` | `0.75` | Height / width ratio. |

#### `save()`

| Name | Type | Default | Description |
|---|---|---|---|
| `fig` | `matplotlib.figure.Figure` | — | Figure to save. |
| `path` | `str \| Path` | — | Base path without extension. |
| `formats` | `list[str] \| None` | `["pdf"]` | File formats to write, e.g. `["pdf", "tiff"]`. |

#### `to_csv()`

| Name | Type | Default | Description |
|---|---|---|---|
| `df` | `pd.DataFrame` | — | Table to export. |
| `path` | `str \| Path` | — | Output CSV path. |
| `decimals` | `int \| dict[str, int]` | `3` | Decimal places — global or per-column. |

#### `to_latex()`

| Name | Type | Default | Description |
|---|---|---|---|
| `df` | `pd.DataFrame` | — | Table to render. |
| `path` | `str \| Path \| None` | `None` | If given, writes the LaTeX string to this file. |
| `caption` | `str \| None` | `None` | Table caption for `\caption{}`. |
| `label` | `str \| None` | `None` | Table label for `\label{}`. |
| `decimals` | `int \| dict[str, int]` | `3` | Decimal places — global or per-column. |
| `units` | `dict[str, str] \| None` | `None` | Per-column units appended to header, e.g. `{"ECD": "µm"}`. |
| `footnotes` | `dict[str, str] \| None` | `None` | Superscript footnotes, e.g. `{"a": "p < 0.05"}`. |

### Returns

- `journal_style()` — context manager, returns `None`.
- `figure_for()` — `matplotlib.figure.Figure` sized to journal column width.
- `save()` — `list[Path]` of the files written.
- `to_csv()` — `None`.
- `to_latex()` — `str` (the LaTeX source); also writes to `path` if provided.

### Raises

| Function | Exception | Condition |
|---|---|---|
| `JournalStyle.__post_init__` | `ValueError` | `preset` is not a recognised built-in preset name. |
| `figure_for` | `ValueError` | `width` is not `"single"`, `"1.5"`, or `"double"`. |
| `save` | `ValueError` | Any entry in `formats` is not a recognised format. |
| `save` | `ValueError` | Parent directory of `path` does not exist. |

### Warns

| Function | Warning | Condition |
|---|---|---|
| `journal_style` | `UserWarning` | The resolved `font_family` is not found by matplotlib and a fallback is used. |

---

## Scientific / algorithmic basis

This module encodes the typographic and visual conventions of high-impact scientific
journals (Nature, Science, Cell, NEJM, JAMA) as a configurable style layer on top of
matplotlib's `rcParams` system.  The conventions are not algorithmic but are
well-established standards: sans-serif fonts (Arial / Helvetica / Helvetica Neue),
7–10 pt text sized for final print dimensions, open axes frames (left + bottom spines
only), outward-pointing tick marks, no gridlines, black-and-white marker and hatch
cycles for series discrimination without colour, and 600 dpi minimum for raster output.
Tables follow the LaTeX `booktabs` convention: three horizontal rules only (top, below
header, bottom), no vertical rules, left-aligned text columns, right-aligned numeric
columns.

The `"default"` preset implements these consensus conventions.  The `"nature"` preset
tightens typography to Nature Publishing Group specifications (7 pt axis labels,
89 / 120 / 180 mm column widths, 300 dpi photos / 600 dpi line art).

**References**

- Rougier N.P., Droettboom M. & Bourne P.E. (2014) *Ten Simple Rules for Better Figures*. PLOS Computational Biology 10(9): e1003833.
- Nature Portfolio (2024) *Guide to Authors — Figures*. nature.com/nature/for-authors/formatting-guide.
- Fear S. (2005) *Publication quality tables in LaTeX*. CTAN: booktabs package documentation.

---

## Behavioral requirements

1. `JournalStyle(preset="default")` constructs without error and exposes resolved (non-`None`) values for all style fields.
2. `JournalStyle(preset="nature")` constructs without error and resolves `single_col_mm` to `89.0`, `font_size` to `7.0`.
3. `JournalStyle(preset="unknown")` raises `ValueError` with a message containing `"unknown"`.
4. A `JournalStyle` field set explicitly (e.g. `font_size=9.0`) overrides the preset value for that field only; all other fields retain the preset value.
5. `journal_style(style)` sets `matplotlib.rcParams` such that `axes.spines.top` and `axes.spines.right` are `False`, `xtick.direction` and `ytick.direction` are `"out"`, and `axes.grid` is `False` for the duration of the block.
6. After exiting `journal_style(style)`, all `rcParams` are restored to the values they had before the block was entered.
7. If the resolved `font_family` is not available in matplotlib's font cache, `journal_style()` emits a `UserWarning` containing the font name before entering the block.
8. `figure_for(style, width="single")` returns a `Figure` with width within ±0.01 inches of `style.single_col_mm / 25.4`.
9. `figure_for(style, width="quarter")` raises `ValueError` with a message containing `"width"`.
10. `save(fig, path, formats=["pdf", "tiff"])` writes `<path>.pdf` and `<path>.tiff` and returns a list of two `Path` objects pointing to those files.
11. `save(fig, path)` where `path.parent` does not exist raises `ValueError` with a message containing the missing directory.
12. `save(fig, path, formats=["bmp"])` raises `ValueError` with a message containing `"bmp"`.
13. `to_latex(df)` returns a string containing `\toprule`, `\midrule`, and `\bottomrule` and no `\hline` and no `|` in the column specification.
14. `to_latex(df, units={"ECD": "µm"})` includes `(µm)` in the rendered column header.
15. `to_latex(df, footnotes={"a": "p < 0.05"})` includes `p < 0.05` in the rendered string.
16. `to_latex(df, path=some_path)` writes the LaTeX string to `some_path` and also returns it.
17. `to_csv(df, path, decimals=2)` writes a CSV where numeric columns are rounded to 2 decimal places.

---

## Parameter validation rules

```python
# JournalStyle.__post_init__
_PRESETS = {"default", "nature"}
if self.preset not in _PRESETS:
    raise ValueError(f"Unknown preset {self.preset!r}. Available: {sorted(_PRESETS)}.")

# figure_for
_WIDTHS = {"single", "1.5", "double"}
if width not in _WIDTHS:
    raise ValueError(f"width must be one of {sorted(_WIDTHS)!r}, got {width!r}.")

# save
_FORMATS = {"pdf", "svg", "eps", "tiff", "png"}
for fmt in formats:
    if fmt not in _FORMATS:
        raise ValueError(f"Unrecognised format {fmt!r}. Supported: {sorted(_FORMATS)}.")
parent = Path(path).parent
if not parent.exists():
    raise ValueError(f"Output directory does not exist: {parent}")
```

---

## Usage example

```python
import pandas as pd
from stamp.io import load
from stamp.stats import describe
from stamp.plot import distribution
from stamp.export import JournalStyle, journal_style, figure_for, save, to_csv, to_latex

ecds = load("grains.csv", column="ECD_um", unit="µm", label="Grain ECD")

# Apply Nature style to an existing plot
style = JournalStyle(preset="nature")
with journal_style(style):
    fig = figure_for(style, width="single", aspect=0.75)
    ax = fig.add_subplot(111)
    distribution(ecds, ax=ax)
    paths = save(fig, "figures/fig1", formats=["pdf", "tiff"])

# Granular override on top of a preset
custom = JournalStyle(preset="nature", font_size=9)

# Export descriptive statistics table
stats = describe(ecds)
df = pd.DataFrame({...})   # build from stats result fields
to_csv(df, "tables/table1.csv")
to_latex(df, "tables/table1.tex", caption="Descriptive statistics.", label="tab:stats",
         units={"Mean": "µm", "Median": "µm"}, decimals=2)
```

---

## Notebook outline

**File:** `notebooks/01_quickstart.ipynb` (new section appended — no new notebook)

### 9. Publication-ready export

Demonstrate applying journal styles to existing STAMP figures generated earlier in
the notebook, then export the summary statistics table from §4.

1. **Default style** — re-render the distribution figure from §2 inside `journal_style(JournalStyle())` and save as PDF.
2. **Nature preset** — re-render the same figure using `JournalStyle(preset="nature")` and show side-by-side with the default to highlight the typographic differences.
3. **Granular override** — show a one-field override (`font_size=9`) on top of the Nature preset.
4. **Table export** — build a `pd.DataFrame` from `stats_result` (§4), call `to_csv()` and `to_latex()`, and print the LaTeX output inline.

---

## Files affected

| File | Change |
|---|---|
| `src/stamp/export.py` | New module — `JournalStyle`, `journal_style`, `figure_for`, `save`, `to_csv`, `to_latex` |
| `src/stamp/__init__.py` | Re-export `JournalStyle` and all public functions from `stamp.export` |
| `tests/test_export.py` | New test file covering requirements 1–17 |
| `notebooks/01_quickstart.ipynb` | Add §9 Publication-ready export |
| `docs/examples.md` | Update §01_quickstart description to mention the new export section |
| `CHANGELOG.md` | Add bullet under `[Unreleased]` |

---

## Approval checklist

- [ ] Spec reviewed and signed off by author
- [ ] API signature finalised (no breaking changes to existing functions)
- [ ] All behavioral requirements are testable
- [ ] Notebook section outline agreed (or confirmed not needed)
- [ ] Ready to enter Plan mode
