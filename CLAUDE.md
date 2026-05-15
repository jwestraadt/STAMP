# STAMP — Claude Code Instructions

## Project overview

STAMP is a scientific Python package. Source lives in `src/stamp/`, tests in `tests/`, docs in `docs/`.
Package manager: **uv**. Build backend: **hatchling** (version driven by git tags via hatch-vcs).

---

## Dev environment

```bash
uv sync --all-extras   # install all deps including dev
```

All commands below are run via `uv run <tool>` so they use the project venv.

---

## Before every commit — mandatory checklist

Run these in order and fix any failures before committing:

```bash
uv run ruff format .                          # auto-format
uv run ruff check . --fix                     # lint + auto-fix
uv run pytest                                 # all tests must pass
```

Then:
1. **Update `CHANGELOG.md`** — add a bullet under `[Unreleased]` describing what changed.
2. **Write the commit message** in Conventional Commits format (see below).

---

## Commit message format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`
Examples:
- `feat(core): add Fourier transform utility`
- `fix(io): handle missing file extension gracefully`
- `docs(api): add NumPy docstrings to loader module`
- `test(core): add edge-case tests for normalisation`

---

## Code style

- **Formatter / linter:** Ruff (config in `pyproject.toml`) — 88-char lines, Python 3.9 target.
- **Type hints:** Required on all public functions and methods.
- **Imports:** Sorted automatically by Ruff (isort-compatible). Never add `# noqa` without a comment explaining why.

---

## Docstrings — NumPy style

Every public function, class, and method must have a NumPy-style docstring:

```python
def compute(data: np.ndarray, axis: int = 0) -> np.ndarray:
    """Compute the mean along an axis.

    Parameters
    ----------
    data : np.ndarray
        Input array.
    axis : int, optional
        Axis along which to compute the mean. Default is 0.

    Returns
    -------
    np.ndarray
        Array of means.

    Raises
    ------
    ValueError
        If `axis` is out of range for `data`.

    Examples
    --------
    >>> compute(np.array([[1, 2], [3, 4]]))
    array([2., 3.])
    """
```

Private functions (prefixed `_`) do not require full docstrings but should have a one-line summary.

---

## Testing

- Tests live in `tests/`. Mirror the `src/stamp/` structure: `src/stamp/core.py` → `tests/test_core.py`.
- Use `pytest` fixtures and parametrize for multiple inputs.
- Every public function must have at least one test.
- Coverage threshold: 60% (raise as the codebase grows).

```bash
uv run pytest                        # run all tests
uv run pytest tests/test_core.py     # single file
uv run pytest -k "test_name"         # single test
uv run pytest --cov=stamp --cov-report=html   # HTML coverage report
```

---

## Documentation

- Docs are built with Sphinx. Source in `docs/`, output in `docs/_build/` (gitignored).
- New public modules must be importable by sphinx-autoapi automatically — no manual `.rst` edits needed.
- For narrative docs (tutorials, how-tos) add `.md` files in `docs/` and reference them in `docs/index.rst`.
- **Every new notebook must be documented in `docs/examples.md`** — add a section with a short description and representative code snippets. Then verify the docs build cleanly.

**Prerequisite:** [Pandoc](https://pandoc.org/installing.html) must be installed system-wide (used by nbsphinx to convert notebook Markdown cells).

```bash
uv run sphinx-build -W -E -b html docs docs/_build/html   # -W = warnings as errors, -E = always rebuild from scratch
```

---

## Changelog rules

File: `CHANGELOG.md` — follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

- All changes go under `[Unreleased]` until a release is cut.
- Categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- One bullet per logical change. Reference the relevant function/module.
- **Write for users, not developers.** Each entry must describe what the user can now *do*, not how it is implemented. Omit: internal dataclass names, test counts, coverage percentages, dev-only dependency additions, docstring/RST fixes, and file renames that have no user-visible effect.
- Group related entries under bold sub-headings (e.g. **Stereology**, **Statistics**, **Plots**) when a section has more than three bullets.

Example entry:
```markdown
## [Unreleased]

### Added

**Stereology**
- Saltykov/Wicksell matrix unfolding — recovers the 3-D sphere-diameter distribution
  from 2-D section measurements (`stamp.stereo.saltykov()`)
```

---

## Release process

1. Update `CHANGELOG.md`: rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`, add new `[Unreleased]` section.
2. Commit: `chore(release): bump version to vX.Y.Z`
3. Tag: `git tag vX.Y.Z`
4. Push tag: `git push origin vX.Y.Z` — this triggers the PyPI publish workflow automatically.

---

## Data model — canonical patterns (read before touching io / stats / stereo / plot / pipeline)

**This is the single authoritative design. Do not introduce alternative implementations.**

### Public boundary: `pd.DataFrame` with attrs

`stamp.io.load()` returns a **single-column `pd.DataFrame`**.  Two metadata keys are always
set on the frame:

```python
df.attrs["unit"]   # str — physical unit, e.g. "µm"
df.attrs["label"]  # str — display name,  e.g. "Grain ECD"
```

The column itself is named after `label`.  All downstream public functions (`stamp.stats.*`,
`stamp.stereo.*`, `stamp.plot.*`) accept this DataFrame directly — callers never unwrap it.

`stamp.io.load_mipar_features()` returns the **full MIPAR table** as a plain `pd.DataFrame`
(multiple columns, no attrs).  It is not a measurement container; pass individual columns to
`_coerce_to_measurement` or use `stamp.pipeline.run_mipar()` to process it.

### Internal adapter: `_coerce_to_measurement`

Every public stats / stereo / plot function that takes a `data` argument must call
`_coerce_to_measurement(data)` as its **first line** (imported from `stamp._types`).  This
converts a single-column `pd.DataFrame` or an attrs-labelled `pd.Series` to a
`MeasurementData` transparently.  A bare `MeasurementData` is passed through unchanged.

Do **not** bypass this by adding separate `isinstance` branches inside public functions.

### Internal representation: `MeasurementData`

All computation (stereo unfolding, stats CI methods, KDE, plots) operates on `MeasurementData`:

```python
@dataclass
class MeasurementData:
    values: np.ndarray  # 1-D float64, all finite, all > 0
    unit: str
    label: str
```

`MeasurementData` is re-exported from `stamp` for users who need it (e.g. simulation output),
but it is **not** the return type of `load()`.

### Pipeline internal: `pd.Series` with attrs

Inside `stamp.pipeline`, per-FOV data is stored as a `pd.Series` with attrs (not a
`MeasurementData` and not a `pd.DataFrame`).  Use the two private helpers — never construct
these series ad-hoc:

```python
_make_series(values: np.ndarray, unit: str, label: str) -> pd.Series
_series_to_measurement(series: pd.Series) -> MeasurementData
```

`FieldResult.data` is a `pd.Series`.  Access metadata via `fr.data.attrs["unit"]` and
`fr.data.attrs["label"]`, **not** `.unit` / `.label` attribute access.

### `TYPE_CHECKING` guard for pandas in `_types.py`

`_types.py` does not import pandas at module level.  The `pd` annotation in
`_coerce_to_measurement` is guarded with:

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pandas as pd
```

This keeps `_types.py` lean and avoids a circular import.  Do not add a top-level
`import pandas as pd` to `_types.py`.

---

## Project structure

```
src/stamp/          # package source — all public API lives here
tests/              # pytest tests — mirrors src/stamp/ layout
docs/               # Sphinx documentation source
.github/workflows/  # CI (ci.yml) and PyPI publish (publish.yml)
pyproject.toml      # single config file for build, deps, ruff, pytest
CHANGELOG.md        # all notable changes
CITATION.cff        # machine-readable citation metadata
```
