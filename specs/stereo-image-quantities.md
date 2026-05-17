# Spec: `stamp.stereo` — image-level stereological quantities

> **Status:** implemented
> **Author:** Johan Westraadt
> **Branch:** `feat/io-mipar-image`

---

## One-line summary

Derive volume fraction, surface area density, mean caliper diameter, and 3-D mean
free path from MIPAR image-level measurements (`stamp.stereo.volume_fraction`,
`surface_area_density`, `mean_caliper_diameter`, `mean_free_path_3d`).

---

## Public API

```python
def volume_fraction(
    area_fraction_pct: float | np.ndarray,
) -> float | np.ndarray: ...

def surface_area_density(
    vv: float | np.ndarray,
    l_alpha_um: float | np.ndarray,
) -> float | np.ndarray: ...

def mean_caliper_diameter(
    l_alpha_um: float | np.ndarray,
) -> float | np.ndarray: ...

def mean_free_path_3d(
    vv: float | np.ndarray,
    sv: float | np.ndarray,
) -> float | np.ndarray: ...
```

### Parameters

| Name | Type | Description |
|---|---|---|
| `area_fraction_pct` | `float` or `np.ndarray` | Areal fraction in % (0–100). |
| `vv` | `float` or `np.ndarray` | Volume fraction in [0, 1). |
| `l_alpha_um` | `float` or `np.ndarray` | Mean intercept length through objects (µm). Must be > 0. |
| `sv` | `float` or `np.ndarray` | Surface area density (µm⁻¹). Must be > 0. |

### Returns

All four functions return `float | np.ndarray` matching the shape of the input.
Scalar input → scalar output; array input → array output (NaN propagates).

### Raises

| Function | Exception | Condition |
|---|---|---|
| `volume_fraction` | `ValueError` | any value outside [0, 100] |
| `surface_area_density` | `ValueError` | any `vv` outside [0, 1] or `l_alpha_um` ≤ 0 |
| `mean_caliper_diameter` | `ValueError` | any `l_alpha_um` ≤ 0 |
| `mean_free_path_3d` | `ValueError` | any `vv` outside [0, 1) or `sv` ≤ 0 |

---

## Scientific / algorithmic basis

All relations follow from fundamental stereological principles for isotropic,
uniform, random (IUR) test lines on a statistically homogeneous microstructure.

**Volume fraction** — Delesse (1848) and Glagolev (1933):
$V_V = A_A = \text{Area Fraction (\%)} / 100$

**Surface area density** — Underwood (1970):
$S_V = \frac{4 V_V}{\bar{L}_\alpha}$
where $\bar{L}_\alpha$ is the mean intercept length through the phase of interest
(MIPAR: *Mean Intercept – Objects (Random)*).

**Mean caliper diameter** — Fullman (1953), assumes convex equiaxed particles:
$\bar{D} = \frac{3}{2}\,\bar{L}_\alpha$

Equivalently $\bar{D} = 6 V_V / S_V$.  The factor 3/2 is exact for spheres
and a reasonable approximation for near-equiaxed precipitates.

**3-D mean free path** (interparticle spacing) — Underwood (1970):
$\lambda_{3\mathrm{D}} = \frac{4\,(1-V_V)}{S_V} = \bar{L}_\alpha \cdot \frac{1-V_V}{V_V}$

For isotropic microstructures this equals the mean intercept through the matrix
phase, which MIPAR measures directly as *Mean Intercept – Holes (Random)*.

**References**

- Delesse, A. (1848) *Ann. Mines* 13, 379–388.
- Fullman, R.L. (1953) *Trans. AIME* 197, 447–452.
- Underwood, E.E. (1970) *Quantitative Stereology*. Addison-Wesley.

---

## Behavioral requirements

1. `volume_fraction(50.0)` returns approximately `0.5`.
2. `surface_area_density(0.05, 0.5)` returns `4 × 0.05 / 0.5 = 0.4`.
3. `mean_caliper_diameter(0.5)` returns `0.75` (= 3/2 × 0.5).
4. `mean_free_path_3d(0.05, 0.4)` returns `4 × 0.95 / 0.4 = 9.5`.
5. All four functions accept `np.ndarray` input and return `np.ndarray` of the same shape.
6. NaN values in array inputs propagate to NaN in the output without raising.
7. `volume_fraction` raises `ValueError` when any value is outside [0, 100].
8. `surface_area_density` raises `ValueError` when any `l_alpha_um` ≤ 0.
9. `mean_caliper_diameter` raises `ValueError` when any `l_alpha_um` ≤ 0.
10. `mean_free_path_3d` raises `ValueError` when any `sv` ≤ 0.
11. Functions can be applied column-wise to a `pd.DataFrame` via `df[col].values`.

---

## Parameter validation rules

```python
# volume_fraction
arr = np.asarray(area_fraction_pct, dtype=float)
if np.any((arr < 0) | (arr > 100)):
    raise ValueError(...)

# surface_area_density
if np.any(np.asarray(l_alpha_um, dtype=float) <= 0):
    raise ValueError(...)

# mean_caliper_diameter
if np.any(np.asarray(l_alpha_um, dtype=float) <= 0):
    raise ValueError(...)

# mean_free_path_3d
if np.any(np.asarray(sv, dtype=float) <= 0):
    raise ValueError(...)
```

NaN values are excluded from range checks (NaN comparisons return False).

---

## Usage example

```python
from stamp.stereo import (
    volume_fraction, surface_area_density,
    mean_caliper_diameter, mean_free_path_3d,
)

df["V_V"]             = volume_fraction(df["Area Fraction (%)"])
df["S_V (1/um)"]      = surface_area_density(df["V_V"], df["Mean Intercept - Objects (Random) (um)"])
df["D_bar (um)"]      = mean_caliper_diameter(df["Mean Intercept - Objects (Random) (um)"])
df["lambda_3D (um)"]  = mean_free_path_3d(df["V_V"], df["S_V (1/um)"])
```

---

## Notebook outline

**File:** `notebooks/05_mipar_image_analysis.ipynb` (extend existing notebook)

- Section 5: Derive 3-D quantities per FOV (vectorised column operations on `df_all`)
- Section 6: 3-D summary tables (mean ± std across FOVs, exported as CSV + LaTeX)
- Section 7: 3-D box plots per phase (Nature journal style, same layout as 2-D)

---

## Files affected

| File | Change |
|---|---|
| `src/stamp/stereo.py` | Add four image-level stereology functions |
| `tests/test_stereo.py` | Add tests for requirements 1–11 |
| `notebooks/05_mipar_image_analysis.ipynb` | Add sections 5–7 |
| `specs/stereo-image-quantities.md` | This file |
| `CHANGELOG.md` | Add bullet under `[Unreleased]` |
