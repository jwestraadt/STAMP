# Spec: `stamp.io.load_mipar_image()`

> **Status:** approved
> **Author:** Johan Westraadt
> **Branch:** `feat/io-mipar-image`

---

## One-line summary

Load a MIPAR image-measurement CSV (one row per FOV, all phases as column suffixes)
into a tidy long-format `pd.DataFrame` with one row per (FOV × phase) combination
(`stamp.io.load_mipar_image()`).

---

## Public API

```python
def load_mipar_image(
    path: str | Path,
    *,
    phases: list[str] | None = None,
    drop_columns: list[str] | None = None,
    rename_columns: dict[str, str] | None = None,
) -> pd.DataFrame:
    ...
```

### Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| `path` | `str \| Path` | — | Path to the MIPAR image-measurement CSV. |
| `phases` | `list[str] \| None` | `None` | Phases to retain. `None` auto-detects all phases from column names. |
| `drop_columns` | `list[str] \| None` | `None` | Measurement columns to drop from the output after melting (phase suffix already stripped). |
| `rename_columns` | `dict[str, str] \| None` | `None` | Rename map applied to measurement columns after melting, e.g. `{"Area Fraction (%)": "Vv (%)"}`. |

### Returns

`pd.DataFrame` — tidy long-format table with columns:

| Column | dtype | Description |
|---|---|---|
| `Image` | `str` | FOV filename (original value from the CSV `Image` column). |
| `Phase` | `str` | Phase name parsed from the column suffix, e.g. `"M23C6"`. |
| `Area Fraction (%)` | `float` | Areal phase fraction (%). |
| `Number Density (features/um^2)` | `float` | Feature number density per µm². |
| `Mean Intercept - Objects (Random) (um)` | `float` | Mean random linear intercept through objects (µm). |
| `Mean Intercept - Holes (Random) (um)` | `float` | Mean random linear intercept through matrix/holes (µm). |
| `Mean Inverse Intercept - Objects (Random) (1/um)` | `float` | Mean inverse intercept (= N_L) for objects (µm⁻¹). |
| `Mean Inverse Intercept - Holes (Random) (1/um)` | `float` | Mean inverse intercept for holes (µm⁻¹). |
| `Mode Intercept - Objects (Random) (um)` | `float` | Modal intercept through objects (µm). |
| `Mode Intercept - Holes (Random) (um)` | `float` | Modal intercept through holes (µm). |
| `Mode Inverse Intercept - Objects (Random) (1/um)` | `float` | Modal inverse intercept for objects (µm⁻¹). |
| `Mode Inverse Intercept - Holes (Random) (1/um)` | `float` | Modal inverse intercept for holes (µm⁻¹). |
| `ASTM Grain Size Number (Random Lines)` | `float` | ASTM grain size number. |
| `Total Line Length (Random) (um)` | `float` | Total random test-line length used (µm). |
| `Total Intersections (Random)` | `float` | Total phase boundary intersections counted. |

Additional columns may appear if the source file contains extra measurements.
`drop_columns` and `rename_columns` are applied after melting.

### Raises

| Exception | Condition |
|---|---|
| `ValueError` | File is empty or contains only a header row. |
| `ValueError` | Any entry in `phases` is not found in the auto-detected phase list; message contains the unrecognised phase name. |
| `ValueError` | Any entry in `drop_columns` is not present in the melted DataFrame; message contains the unrecognised column name. |

---

## Scientific / algorithmic basis

MIPAR image-measurement CSVs store one row per field-of-view and encode both the
measurement type and the phase name in each column header using the separator
` - <Phase>` (e.g. `Area Fraction (%) - M23C6`).  `load_mipar_image` parses phase
names by splitting on this separator, groups columns by phase, and melts the wide
table to long format using `pd.melt` / `pd.concat`, yielding one row per
(FOV × phase) combination.  Trailing empty columns produced by a trailing comma in
the CSV header are silently dropped.  Individual NaN cells are preserved; no rows
are dropped.

**References**

N/A — this is a data-loading utility; no stereological equations are applied.

---

## Behavioral requirements

1. Given a valid CSV, returns a `pd.DataFrame` with columns `Image`, `Phase`, and
   all measurement columns with the phase suffix stripped.
2. The number of rows equals `n_FOVs × n_phases` (before any `phases` filter).
3. Phases are auto-detected from column names; the detected set equals the unique
   suffixes after the last ` - ` separator.
4. Given `phases=["M23C6"]`, only rows where `Phase == "M23C6"` are returned.
5. Given `phases=["Unknown"]` where `"Unknown"` is not in the file, raises
   `ValueError` with a message containing `"Unknown"`.
6. Given `drop_columns=["ASTM Grain Size Number (Random Lines)"]`, that column is
   absent from the output DataFrame.
7. Given `drop_columns=["NonExistent"]`, raises `ValueError` with a message
   containing `"NonExistent"`.
8. Given `rename_columns={"Area Fraction (%)": "Vv (%)"}`, the output column is
   named `"Vv (%)"` and `"Area Fraction (%)"` is absent.
9. A CSV with a trailing empty column (trailing comma in header) loads without
   error; the empty column is not present in the output.
10. A row containing one or more NaN cells is retained; the NaN values are
    preserved as `float("nan")`.
11. Given an empty file or a file containing only a header row, raises `ValueError`
    with a message containing `"empty"`.
12. The `Image` column contains the original filename string exactly as written in
    the CSV.

---

## Parameter validation rules

```python
# phases validation (after auto-detection)
if phases is not None:
    detected = _detect_phases(df)
    unknown = [p for p in phases if p not in detected]
    if unknown:
        raise ValueError(
            f"Phase(s) not found in file: {unknown}. Detected: {sorted(detected)}."
        )

# drop_columns validation (after melting)
if drop_columns is not None:
    missing = [c for c in drop_columns if c not in melted.columns]
    if missing:
        raise ValueError(
            f"Column(s) not found in melted DataFrame: {missing}. "
            f"Available: {sorted(melted.columns)}."
        )
```

---

## Usage example

```python
from stamp.io import load_mipar_image

df = load_mipar_image("data/GOO220_52_BatchMeas.csv")
print(df.columns.tolist())   # ['Image', 'Phase', 'Area Fraction (%)', ...]
print(df["Phase"].unique())  # ['M23C6', 'MX ZPhase', 'Laves']
print(df.shape)              # (30, 16)  — 10 FOVs × 3 phases

# Filter to one phase, drop ASTM column, rename area fraction
df_m23 = load_mipar_image(
    "data/GOO220_52_BatchMeas.csv",
    phases=["M23C6"],
    drop_columns=["ASTM Grain Size Number (Random Lines)"],
    rename_columns={"Area Fraction (%)": "Vv (%)"},
)
```

---

## Notebook outline

**File:** `notebooks/05_mipar_image_analysis.ipynb`

1. **Load image measurements** — call `load_mipar_image()` for each of
   `GOO220_51_BatchMeas.csv`, `GOO220_52_BatchMeas.csv`, `GOO220_53_BatchMeas.csv`
   and tag each with a `State` column before concatenating into a single DataFrame.
2. **Inspect the data** — show `.head()`, `.dtypes`, and detected phases.
3. **Stereological calculations** — for each phase in `["M23C6", "MX ZPhase", "Laves"]`,
   filter the combined DataFrame and compute per-FOV columns:
   - **2-D**: volume/area fraction (`stamp.stereo.volume_fraction()`), caliper diameter
     (`stamp.stereo.caliper_diameter()`), 2-D mean free path
     (`stamp.stereo.mean_free_path_2d()`), 2-D interparticle spacing
     (`stamp.stereo.interparticle_spacing_2d()`)
   - **3-D**: surface area density Sv (`stamp.stereo.surface_area_density()`),
     3-D mean free path (`stamp.stereo.mean_free_path_3d()`), 3-D interparticle
     spacing (`stamp.stereo.interparticle_spacing_3d()`)
4. **Box plots — per phase** — for each of the three phases separately, produce a
   multi-panel Nature-style figure (via `stamp.export.journal_style(NATURE)`) with
   one panel per stereological quantity, comparing GOO220_51 vs GOO220_52 vs
   GOO220_53 side by side. Each phase yields its own figure (3 figures total).
5. **Summary table** — for each phase, build a summary DataFrame (mean ± std across
   FOVs per state) and export as CSV and LaTeX via `stamp.export.to_latex()`.

---

## Files affected

| File | Change |
|---|---|
| `src/stamp/io.py` | Add `load_mipar_image()` |
| `src/stamp/__init__.py` | Re-export `load_mipar_image` |
| `tests/test_io.py` | Add tests for requirements 1–12 |
| `notebooks/05_mipar_image_analysis.ipynb` | New notebook |
| `docs/examples.md` | Add section for notebook 05 |
| `CHANGELOG.md` | Add bullet under `[Unreleased]` |

---

## Approval checklist

- [x] Spec reviewed and signed off by author
- [x] API signature finalised (no breaking changes to existing functions)
- [x] All behavioral requirements are testable
- [x] Notebook section outline agreed (or confirmed not needed)
- [x] Ready to enter Plan mode

---

## Before writing any code

After plan approval, create a git worktree for the feature branch so `main` stays
clean and runnable throughout development:

```bash
git worktree add ../stamp-feat-mipar-image -b feat/io-mipar-image
cd ../stamp-feat-mipar-image
```

Within Claude Code, use `EnterWorktree` to switch into the isolated context.
Remove the worktree after the PR is merged:

```bash
git worktree remove ../stamp-feat-mipar-image
```
