# Spec: `stamp.<module>.<function_name>()`

> **Status:** draft | approved | implemented
> **Author:** <!-- your name -->
> **Branch:** `feat/<module>-<short-desc>`

---

## One-line summary

<!-- What the user can now DO. Written for the CHANGELOG. -->
<!-- Example: "Recover the 3-D sphere-diameter distribution from 2-D section data (`stamp.stereo.saltykov()`)" -->

---

## Public API

```python
def function_name(
    data: MeasurementData | pd.DataFrame,
    param_a: float,
    param_b: int = 10,
    *,
    keyword_only: str = "default",
) -> ReturnType:
    ...
```

### Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| `data` | `MeasurementData` or single-column `pd.DataFrame` | — | Input measurements. |
| `param_a` | `float` | — | … |
| `param_b` | `int` | `10` | … |
| `keyword_only` | `str` | `"default"` | … |

### Returns

`ReturnType` — description of what is returned and its fields.

> If a new dataclass is needed, define it in `stamp._types` and re-export from `stamp.__init__`.

### Raises

| Exception | Condition |
|---|---|
| `ValueError` | `param_a <= 0` |
| `ValueError` | `param_b < 2` |

---

## Scientific / algorithmic basis

<!-- One paragraph describing the method. Include the key formula if relevant. -->
<!-- Use LaTeX inline notation: $ECD = 2\sqrt{A/\pi}$ -->

**References**

- Author (Year) *Journal* vol, pages.

---

## Behavioral requirements

Numbered, testable, observable statements.  Each maps to one or more `pytest` test cases.

1. Given a valid `MeasurementData` input, the function returns a `ReturnType` with …
2. Given a single-column `pd.DataFrame` from `stamp.io.load()`, the function produces the same result as when passed a `MeasurementData` directly.
3. Given `param_a <= 0`, the function raises `ValueError` with a message containing "param_a".
4. Given `param_b < 2`, the function raises `ValueError`.
5. Given `seed=<int>`, repeated calls return identical results.
6. <!-- add more as needed -->

---

## Parameter validation rules

```python
if param_a <= 0:
    raise ValueError(f"param_a must be positive, got {param_a}.")
if param_b < 2:
    raise ValueError(f"param_b must be >= 2, got {param_b}.")
```

---

## Usage example

```python
from stamp.io import load
from stamp.<module> import function_name

data = load("grains.csv", column="ECD_um", unit="µm", label="Grain ECD")
result = function_name(data, param_a=1.5, param_b=12)

print(result.some_field)   # expected output
```

---

## Notebook outline (if required)

> Omit this section if no new notebook is needed.

**File:** `notebooks/NN_<topic>.ipynb`

1. **Introduction** — what the method does and when to use it.
2. **Synthetic data** — generate with `stamp.simulate.simulate_section(seed=0)`.
3. **Apply `function_name`** — show the call and print key result fields.
4. **Visualise** — call the corresponding `stamp.plot.*` function.
5. **Interpretation** — one-paragraph summary of what the output means.

---

## Files affected

| File | Change |
|---|---|
| `src/stamp/<module>.py` | Add `function_name()` |
| `src/stamp/_types.py` | Add `ReturnType` dataclass (if new) |
| `src/stamp/__init__.py` | Re-export `ReturnType` (if new) |
| `tests/test_<module>.py` | Add tests for requirements 1–N |
| `notebooks/NN_<topic>.ipynb` | New notebook (if required) |
| `docs/examples.md` | Add notebook section (if required) |
| `CHANGELOG.md` | Add bullet under `[Unreleased]` |

---

## Approval checklist

- [ ] Spec reviewed and signed off by author
- [ ] API signature finalised (no breaking changes to existing functions)
- [ ] All behavioral requirements are testable
- [ ] Notebook section outline agreed (or confirmed not needed)
- [ ] Ready to enter Plan mode
