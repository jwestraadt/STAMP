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

```bash
uv run sphinx-build docs docs/_build/html -W   # -W turns warnings into errors
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
