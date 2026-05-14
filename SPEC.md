# STAMP — Package Specification

## Overview

STAMP is a scientific Python package for 2D quantitative microstructural analysis and
stereological correction. It ingests per-feature measurements (grain areas, equivalent circle
diameters, precipitate sizes, linear intercepts) from common file formats, applies stereological
corrections to estimate 3D size distributions, computes descriptive statistics with confidence
intervals, fits statistical distributions, and produces publication-ready figures.

The stereological methods and statistical approaches follow those implemented in
[GrainSizeTools](https://github.com/marcoalopez/GrainSizeTools) (Lopez-Sanchez, 2018).

---

## Scope

**In scope (v0.x)**

- File I/O: CSV, Excel (`.xlsx` / `.xls`), plain text (`.txt`, `.tsv`)
- Stereological corrections: Saltykov sphere-size unfolding, two-step lognormal fitting,
  linear intercept → grain size (Fullman 1953)
- Statistics: arithmetic mean, geometric mean, median, KDE mode — each with confidence intervals
- Distribution fitting: normal and log-normal via MLE + KS goodness-of-fit
- Visualisation: distribution histograms with KDE overlay, Saltykov dual-panel plot,
  two-step lognormal plot, Q-Q plot

**Deferred (later versions)**

- HDF5 / vendor EBSD format support
- Anisotropy / non-equiaxed grain corrections beyond Fullman factor
- Area-weighted distributions
- Paleopiezometry / differential stress estimation

---

## Module structure

```
src/stamp/
├── _types.py    # shared dataclasses (MeasurementData, results)
├── io.py        # data loading
├── stereo.py    # stereological corrections
├── stats.py     # descriptive statistics + distribution fitting
└── plot.py      # visualisation
```

All public dataclasses and result types are re-exported from `stamp` directly so users never
need to import from `stamp._types`.

---

## Data model

### `MeasurementData`

```python
@dataclass
class MeasurementData:
    values: np.ndarray   # 1-D, dtype float64, all finite, all > 0
    unit: str            # e.g. "µm", "µm²"
    label: str           # human-readable name, e.g. "Grain ECD"
```

**Invariants**

- `values` is always 1-D, `dtype=float64`, all finite, all strictly positive.
- `unit` is a non-empty string. The package never converts between unit systems — the caller
  is responsible for consistent units.
- Functions that transform `values` return a **new** `MeasurementData`; the original is
  never mutated.

---

## `stamp.io`

### `load(path, column, unit, label, delimiter, skip_rows, sheet_name) → MeasurementData`

Load a single column of positive measurements from a delimited text or Excel file.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str \| Path` | — | Path to `.csv`, `.txt`, `.tsv`, `.xlsx`, or `.xls` |
| `column` | `str \| int` | — | Column name (str) or 0-based index (int) |
| `unit` | `str` | — | Physical unit string, e.g. `"µm"` or `"µm²"` |
| `label` | `str \| None` | `None` | Display label; defaults to column name if str, else `"Feature"` |
| `delimiter` | `str \| None` | `None` | Field separator for text files; auto-detected if `None` |
| `skip_rows` | `int` | `0` | Rows to skip before the header |
| `sheet_name` | `str \| int` | `0` | Excel sheet name or 0-based index (ignored for text files) |

**Returns** `MeasurementData`

**Raises**

- `FileNotFoundError` — path does not exist
- `ValueError` — unsupported file extension, column not found, or no valid values remain

**Behaviour**

- Non-finite values (NaN, ±inf) and values ≤ 0 are silently dropped; a
  `warnings.warn` states the count of removed rows.
- Supported extensions: `.csv`, `.txt`, `.tsv` (pandas `read_csv`); `.xlsx`, `.xls`
  (pandas `read_excel`).

---

## `stamp.stereo`

### `ecd_from_area(data) → MeasurementData`

Convert 2D projected areas to equivalent circle diameters.

```
ECD = 2 × √(area / π)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `MeasurementData` | Areas; unit should be a length² string (not enforced) |

**Returns** `MeasurementData` — diameters; unit is derived by stripping a trailing `²`
(e.g. `"µm²"` → `"µm"`). Label becomes `"ECD"`.

**Raises** `ValueError` — if any value is non-positive.

---

### `linear_intercept_correction(data) → MeasurementData`

Apply the Fullman (1953) correction to convert 2D linear intercept lengths to estimated
3D grain diameters, assuming equiaxed grains (ASTM E112).

```
D = (4 / π) × L
```

applied element-wise to the full chord-length distribution.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `MeasurementData` | Linear intercept chord lengths |

**Returns** `MeasurementData` — corrected grain diameters; label becomes
`"Corrected Grain Diameter"`.

**Notes** — The factor 4/π ≈ 1.273 assumes equiaxed grains. For non-equiaxed
microstructures, apply anisotropy corrections externally before passing data to this
function.

---

### `saltykov(data, n_bins, left_edge) → SaltykovResult`

Convert a 2D circle-diameter distribution to a 3D sphere-diameter distribution using the
Saltykov (1967) matrix unfolding method based on Wicksell's (1925) cross-section
probability equation.

**Algorithm**

1. Bin the 2D diameters into `n_bins` equal-width classes.
2. For each class *i* (coarsest to finest), compute the Wicksell cross-section probability:

   ```
   P(r₁ < r < r₂ | R) = (1/R) × [√(R² - r₁²) - √(R² - r₂²)]
   ```

   where *R* is the sphere radius (bin midpoint), *r₁*, *r₂* are the 2D class bounds.

3. Subtract the contribution of coarser classes from the observed 2D frequency of class *i*
   to obtain the 3D frequency.
4. Clip any negative unfolded frequencies to zero (with `warnings.warn`) and normalise so
   the distribution integrates to one.
5. Compute a volume-weighted cumulative distribution: weight each 3D frequency by *d³*
   (assuming spherical grains), then normalise cumulatively to 100 %.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | 2D circle diameters |
| `n_bins` | `int` | `10` | Number of equal-width bins; must be in [3, 25] |
| `left_edge` | `float \| str` | `0` | Lower histogram bound; pass `"min"` to use `data.values.min()` |

**Returns**

```python
@dataclass
class SaltykovResult:
    bin_midpoints: np.ndarray    # 3D sphere diameter bin centres
    bin_edges: np.ndarray        # bin edges (length n_bins + 1)
    bin_width: float             # constant bin width
    freq3d: np.ndarray           # normalised 3D frequency density
    cdf_vol: np.ndarray          # volume-weighted cumulative distribution (0–100 %)
    unit: str                    # inherited from input
    label: str                   # inherited from input
```

**Raises**

- `ValueError` — `n_bins` outside [3, 25]
- `ValueError` — fewer unique values than `n_bins`

**References** — Saltykov (1967); Wicksell (1925); Schwartz (1934); Sahagian &
Proussevitch (1998); Higgins (2000).

---

### `two_step(data, bin_range) → TwoStepResult`

Estimate the best-fit lognormal parameters for a 3D grain size distribution by iterating
the Saltykov unfolding over a range of bin counts and minimising the lognormal fitting
error. Follows the two-step method of Lopez-Sanchez & Llana-Funez (2016).

**Algorithm**

1. For each `n_bins` in `bin_range`, run `saltykov()` and fit a lognormal PDF to the
   resulting `freq3d` vs `bin_midpoints` via nonlinear least-squares
   (Levenberg–Marquardt).
2. Select the `n_bins` value that minimises the residual sum of squares.
3. Compute parameter uncertainty from the covariance matrix; derive ±3σ error bounds on
   the fitted curve.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | 2D circle diameters |
| `bin_range` | `tuple[int, int]` | `(10, 20)` | Inclusive range of bin counts to test |

**Returns**

```python
@dataclass
class TwoStepResult:
    geometric_mean: float        # scale parameter of best-fit lognormal
    shape: float                 # multiplicative standard deviation (σ of ln)
    params_err: np.ndarray       # 1-σ uncertainties on (shape, scale)
    best_n_bins: int             # bin count with minimum fitting error
    xgrid: np.ndarray            # x values for fitted curve
    fit_curve: np.ndarray        # best-fit lognormal PDF values
    fit_error: np.ndarray        # ±3σ uncertainty band half-width
    unit: str
    label: str
```

**Raises**

- `ValueError` — `bin_range` values outside [3, 25] or min ≥ max
- `RuntimeError` — lognormal fitting fails to converge for all bin counts

**References** — Lopez-Sanchez & Llana-Funez (2016).

---

## `stamp.stats`

### `amean(data, ci, method) → MeanResult`

Arithmetic mean with confidence interval. Optimal for normally distributed populations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | Input measurements |
| `ci` | `float` | `0.95` | Confidence level in (0, 1) |
| `method` | `str` | `"ASTM"` | CI method: `"ASTM"`, `"GCI"`, or `"mCox"` |

**CI methods**

| Method | Description | Reference |
|--------|-------------|-----------|
| `"ASTM"` | t-distribution CLT per ASTM E112-12: error = t × (σ / √n) | ASTM E112 |
| `"GCI"` | Monte Carlo generalised confidence interval (10 000 runs) | Krishnamoorthy & Mathew (2003) |
| `"mCox"` | Modified Cox method; robust for lognormal data | Armstrong (1992) |

**Returns**

```python
@dataclass
class MeanResult:
    mean: float
    std: float               # Bessel-corrected standard deviation
    ci_low: float
    ci_high: float
    ci_length: float
    n: int
    unit: str
    label: str
```

**Raises** `ValueError` — unknown `method` or `ci` outside (0, 1).

---

### `gmean(data, ci, method) → MeanResult`

Geometric mean with confidence interval. Optimal for log-normally distributed populations.
Computed by log-transforming, computing the arithmetic mean, then back-transforming.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | Input measurements |
| `ci` | `float` | `0.95` | Confidence level |
| `method` | `str` | `"CLT"` | CI method: `"CLT"` or `"bayes"` |

**CI methods**

| Method | Description | Reference |
|--------|-------------|-----------|
| `"CLT"` | CLT on log-transformed data, back-transformed | — |
| `"bayes"` | Bayesian CI via `scipy.stats.bayes_mvs` on log data, back-transformed | Oliphant (2006) |

**Returns** `MeanResult` — `std` field holds the multiplicative standard deviation
(i.e. exp(σ_log)).

---

### `median(data, ci) → MedianResult`

Median with interquartile range and confidence interval.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | Input measurements |
| `ci` | `float` | `0.95` | Confidence level |

**Returns**

```python
@dataclass
class MedianResult:
    median: float
    iqr: float               # interquartile range (Q75 - Q25)
    ci_low: float
    ci_high: float
    ci_length: float
    n: int
    unit: str
    label: str
```

CI computed via the Hollander & Wolfe (1999) rule-of-thumb:
index = (n/2) ± (z × √n) / 2.

---

### `freq_peak(data, bandwidth) → PeakResult`

Estimate the distribution mode using Gaussian kernel density estimation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | Input measurements |
| `bandwidth` | `str \| float` | `"silverman"` | KDE bandwidth: `"silverman"`, `"scott"`, or a positive float |

**Returns**

```python
@dataclass
class PeakResult:
    peak: float              # grain size at density maximum
    peak_density: float      # density value at peak
    xgrid: np.ndarray        # x values used for KDE evaluation
    density: np.ndarray      # KDE density values
    bandwidth: float         # resolved bandwidth value used
    unit: str
    label: str
```

**Raises** `ValueError` — unknown bandwidth string or non-positive float bandwidth.

---

### `fit(data, distribution) → FitResult`

Fit a parametric distribution to the data via maximum likelihood estimation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | Input measurements |
| `distribution` | `str` | `"lognormal"` | `"normal"` or `"lognormal"` |

**Returns**

```python
@dataclass
class FitResult:
    distribution: str
    params: dict             # {"loc": float, "scale": float} for normal;
                             # {"s": float, "loc": float, "scale": float} for lognormal
    r_squared: float         # R² of fitted CDF vs empirical CDF
    ks_statistic: float      # Kolmogorov–Smirnov D statistic
    ks_pvalue: float         # KS p-value; large p → distribution not rejected
    unit: str
    label: str
```

**Raises**

- `ValueError` — `distribution` not `"normal"` or `"lognormal"`
- `RuntimeError` — MLE optimisation fails to converge

---

### `describe(data, ci) → DescribeResult`

Convenience wrapper that calls `amean`, `gmean`, `median`, and `freq_peak` with defaults
and returns all results in one object.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | Input measurements |
| `ci` | `float` | `0.95` | Confidence level passed to all sub-functions |

**Returns**

```python
@dataclass
class DescribeResult:
    n: int
    amean: MeanResult        # method="ASTM"
    gmean: MeanResult        # method="CLT"
    median: MedianResult
    peak: PeakResult         # bandwidth="silverman"
    percentiles: dict        # keys: 5, 10, 25, 75, 90, 95
    unit: str
    label: str
```

---

## `stamp.plot`

All plot functions:

- Return a `matplotlib.figure.Figure`.
- Accept `output_path` (str / Path / None): if given, save the figure at `dpi` resolution;
  format is inferred from the file extension.
- Accept `**kwargs` forwarded to the underlying `Figure` or `Axes` calls for fine-grained
  control.
- Use a consistent publication style: top and right spines hidden; near-black text
  (`#252525`); default DPI 300.

**Default colour palette**

| Element | Hex |
|---------|-----|
| Histogram bars | `#80419d` |
| Histogram edges | `#C59fd7` |
| Line / KDE | `#2F4858` |
| Geometric mean marker | `#fec44f` |
| KDE fill | `#80419d` at α=0.65 |

---

### `distribution(data, plot, avg, bins, bandwidth, fit, output_path, dpi, figsize) → Figure`

Histogram and/or KDE of the 2D measurement distribution with annotated averages.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | Input measurements |
| `plot` | `tuple[str, ...]` | `("hist", "kde")` | Elements to draw; subset of `{"hist", "kde"}` |
| `avg` | `tuple[str, ...]` | `("amean", "gmean", "median", "mode")` | Averages to annotate as vertical lines |
| `bins` | `int \| str` | `"auto"` | Bin count or numpy strategy (`"doane"`, `"fd"`, `"scott"`, etc.) |
| `bandwidth` | `str \| float` | `"silverman"` | KDE bandwidth |
| `fit` | `FitResult \| None` | `None` | If provided, overlays the fitted PDF |
| `output_path` | `str \| Path \| None` | `None` | Save path |
| `dpi` | `int` | `300` | Output resolution |
| `figsize` | `tuple[float, float]` | `(6.4, 4.8)` | Figure size in inches |

**Raises** `ValueError` — unknown element in `plot` or `avg`.

---

### `saltykov_plot(result, output_path, dpi, figsize) → Figure`

Dual-panel figure from a `SaltykovResult`:

- **Left panel** — bar histogram of `freq3d` vs `bin_midpoints`.
- **Right panel** — line + scatter plot of the volume-weighted cumulative distribution
  (`cdf_vol` vs `bin_midpoints`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `result` | `SaltykovResult` | — | Output of `stereo.saltykov()` |
| `output_path` | `str \| Path \| None` | `None` | Save path |
| `dpi` | `int` | `300` | Output resolution |
| `figsize` | `tuple[float, float]` | `(10, 4.8)` | Figure size in inches |

---

### `twostep_plot(result, output_path, dpi, figsize) → Figure`

Single-panel figure from a `TwoStepResult`:

- Hatched bar histogram of the best Saltykov `freq3d`.
- Solid best-fit lognormal curve overlaid.
- Filled ±3σ uncertainty band.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `result` | `TwoStepResult` | — | Output of `stereo.two_step()` |
| `output_path` | `str \| Path \| None` | `None` | Save path |
| `dpi` | `int` | `300` | Output resolution |
| `figsize` | `tuple[float, float]` | `(6.4, 4.8)` | Figure size in inches |

---

### `qq_plot(data, distribution, percent, output_path, dpi, figsize) → Figure`

Quantile-quantile plot comparing the empirical distribution to a theoretical one.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `MeasurementData` | — | Input measurements |
| `distribution` | `str` | `"lognormal"` | `"normal"` or `"lognormal"` |
| `percent` | `float` | `2` | Percentile trim applied to each tail before plotting |
| `output_path` | `str \| Path \| None` | `None` | Save path |
| `dpi` | `int` | `300` | Output resolution |
| `figsize` | `tuple[float, float]` | `(6.4, 4.8)` | Figure size in inches |

**Raises** `ValueError` — unknown `distribution`.

---

## Error-handling policy

| Situation | Behaviour |
|-----------|-----------|
| Bad path, unknown column, wrong enum value | `ValueError` / `FileNotFoundError` with descriptive message |
| Data quality (NaN, ±inf, negatives) | `warnings.warn` stating count removed; continue with cleaned data |
| Saltykov negative unfolded frequencies | `warnings.warn`; clip to zero and renormalise |
| MLE / optimisation failure | `RuntimeError` |

---

## Runtime dependencies

| Package | Purpose |
|---------|---------|
| `numpy` | Array operations |
| `scipy` | Distribution fitting, KDE, KS test, CI methods |
| `pandas` | File I/O |
| `matplotlib` | Plotting |

---

## References

- Saltykov SA (1967) *Stereometric Metallography*. Metallurgizdat, Moscow.
- Wicksell SD (1925) *Biometrika* 17, 84–99.
- Schwartz HA (1934) *Metals & Alloys* 5, 139.
- Sahagian DL & Proussevitch AA (1998) *J. Volcanology* 84, 173–196.
- Higgins MD (2000) *Am. Mineralogist* 85, 1105–1116.
- Fullman RL (1953) *Trans. AIME* 197, 447–452.
- Lopez-Sanchez MA & Llana-Funez S (2016) *Solid Earth* 7, 1197–1212.
- Armstrong BG (1992) *Am. J. Epidemiology* 135, 1309–1316.
- Krishnamoorthy K & Mathew T (2003) *Technometrics* 45, 103–109.
- Hollander M & Wolfe DA (1999) *Nonparametric Statistical Methods*. Wiley.
- Oliphant TE (2006) *Guide to NumPy*. Brigham Young University.
- ASTM E112-12 (2012) Standard Test Methods for Determining Average Grain Size.
