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

## Agentic coding guidance

### Plan mode — use before large changes

Before starting any task that touches more than one module, renames or removes public API, or adds a new module, enter Plan mode first.  Outline the approach, identify affected files, and confirm the design before writing any code.  This avoids costly mid-implementation pivots.

Triggers that require a plan:
- New public module (new file under `src/stamp/`)
- Any change to `_types.py` (affects every module)
- Refactor that touches ≥ 3 files
- Breaking API change (parameter rename, return-type change, removal)

Single-function additions to an existing module do not need a formal plan — proceed directly to implementation.

### Worktrees — use for isolated feature work

Use a git worktree when working on a feature branch so the main checkout stays clean and runnable.  This is especially important when a feature takes multiple sessions or involves executing notebooks mid-development.

```bash
# Create a worktree for the feature branch
git worktree add ../stamp-feat-<name> -b feat/<module>-<name>

# Work in the worktree; main checkout is untouched
cd ../stamp-feat-<name>

# Remove when the PR is merged
git worktree remove ../stamp-feat-<name>
```

Within Claude Code, use the `EnterWorktree` tool to switch into a worktree-isolated context for the session.

### Commit atomicity

Each commit should be a single logical unit that passes the pre-commit checklist on its own.  Do not batch unrelated changes into one commit.  If a notebook and a new function are both part of the feature, commit them together; if a docstring fix is unrelated, it gets its own commit.

---

## Spec-driven development

Write a spec *before* any code.  The spec is the single source of truth that drives implementation, tests, docs, and the PR description, and gives Claude Code an unambiguous brief to work from.

### Workflow

1. **Write the spec** — create `specs/<module>-<feature>.md` from the template at `specs/_template.md`.
2. **Review and approve** — human reads and signs off before any code is written.  This is the cheapest moment to catch wrong API design or a missing parameter.
3. **Enter Plan mode** — hand the approved spec to Claude in Plan mode.  Claude maps each behavioral requirement to specific files, identifies impacts on `_types.py` / `__init__.py`, and flags any ambiguity before implementation starts.
4. **Implement against the spec** — code satisfies the spec's behavioral requirements exactly.  If an implementation decision is not covered by the spec, surface it to the human rather than deciding unilaterally.
5. **Derive tests from the spec** — each numbered behavioral requirement maps to one or more `pytest` test cases, named after the requirement.
6. **Validate against the spec** — after implementation, tick every behavioral requirement: correct return type, all validation rules enforced, docstring matches spec description.
7. **Notebook and docs from the spec** — the notebook section outline was already written in the spec; the CHANGELOG bullet is the spec's one-line summary.
8. **Use the spec as the PR description** — paste the spec's summary, API block, and behavioral requirements checklist directly into the PR body.

### What belongs in a spec

See `specs/_template.md` for the full template.  At minimum a spec must contain:

- Public function signature with all parameter types and the return type
- Scientific / algorithmic basis (one paragraph + references)
- Numbered behavioral requirements (testable, observable statements)
- Parameter validation rules (what raises `ValueError`, what warns)
- A short usage example (3–5 lines)

A spec does **not** contain implementation details — those belong in the code.

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

## Branches, PRs, and merging

### Branch naming

Mirror the Conventional Commits type:

| Work type | Branch name |
|---|---|
| New feature | `feat/<module>-<short-desc>` |
| Bug fix | `fix/<module>-<short-desc>` |
| Docs / notebooks | `docs/<short-desc>` |
| Refactor / CI / chore | `chore/<short-desc>` |

Examples: `feat/stereo-johnson-correction`, `fix/io-xlsx-encoding`, `docs/add-pipeline-notebook`.

### Opening the PR

```bash
gh pr create --title "feat(<module>): <short summary>" --body "$(cat <<'EOF'
## Summary
- <what this adds or fixes — one bullet per logical change>

## Notebooks added
- `notebooks/NN_<topic>.ipynb` — <one-line description>  (omit section if none)

## Test plan
- [ ] `uv run ruff format . && uv run ruff check . --fix`
- [ ] `uv run pytest` — all tests pass, coverage ≥ 60 %
- [ ] Notebook executes end-to-end without errors
- [ ] `uv run sphinx-build -W -E -b html docs docs/_build/html` — no warnings
- [ ] CHANGELOG updated under `[Unreleased]`
EOF
)"
```

Open as a **draft** PR if the branch is still in progress; mark ready for review only when all checklist items are ticked and CI is green.

### Merge strategy

Use **squash merge** on GitHub (`Squash and merge` button).  This keeps `main` history as one commit per feature and preserves the Conventional Commits shape for automated changelogs.  Never use rebase-merge or create-merge-commit for feature work.

### CI failure recovery

When a pushed PR fails CI:

1. Fix the issue locally.
2. Re-run the full pre-commit checklist (`ruff format`, `ruff check`, `pytest`).
3. `git push` — do **not** amend or force-push a branch that already has a PR open; just push a new commit.
4. CI will re-trigger automatically on the new push.

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
- **Use `stamp.simulate.simulate_section()` as the preferred source of synthetic data** in tests and notebooks — it produces a reproducible `SimulationResult` with both `true_diameters` and `apparent_diameters` as `MeasurementData`, with a known ground truth for validating stereological corrections. Always pass `seed=` for reproducibility in tests:

```python
from stamp.simulate import simulate_section

sim = simulate_section(mu=30.0, sigma=0.3, n_intersections=300, seed=42)
# sim.apparent_diameters  → MeasurementData (2-D section measurements)
# sim.true_diameters      → MeasurementData (3-D ground truth)
```

Do not generate raw `np.random` arrays in tests when `simulate_section` covers the case.

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

## Notebook conventions

### Numbering and naming

Notebooks are numbered with a two-digit zero-padded prefix: `01_quickstart.ipynb`, `02_simulation_validation.ipynb`, etc.  Pick the next available number.  Use lowercase with underscores for the topic part.

### Kernel

Register the uv venv as a kernel once per machine:

```bash
uv run python -m ipykernel install --user --name stamp-dev --display-name "STAMP (dev)"
```

All notebooks must use the `stamp-dev` kernel so that CI execution picks up the correct environment.

### Synthetic data in notebooks

Prefer `stamp.simulate.simulate_section()` over bundling external data files when the notebook's purpose is to demonstrate or validate a method.  It produces a fully reproducible dataset with a known ground truth and requires no data file at all:

```python
from stamp.simulate import simulate_section

sim = simulate_section(mu=45.0, sigma=0.35, n_intersections=500, seed=0)
ecds = sim.apparent_diameters   # pass directly to stamp.stereo / stamp.stats / stamp.plot
```

Only use a file in `notebooks/data/` when the notebook demonstrates loading real experimental data.

### Data files

- Input data lives in `notebooks/data/`.  Name files descriptively: `apparent_diameters.txt`, `GOO220_52_FeatureMeas.csv`.
- Notebooks may write pipeline output (plots, CSVs) to a sub-directory of `notebooks/data/`.
- Use this two-path resolution pattern so the notebook runs correctly from both the repo root and the `notebooks/` directory:

```python
from pathlib import Path

data_path = Path("notebooks/data/my_file.csv")
if not data_path.exists():
    data_path = Path("data/my_file.csv")
```

### Cell structure

Every notebook must open with:
1. A **Markdown title cell** — `# STAMP — <Topic>` plus a numbered outline of what the notebook covers.
2. A **single imports cell** containing `%matplotlib inline`, all `import` statements, and `warnings.filterwarnings` if needed.
3. Section cells thereafter, each preceded by a Markdown header (`## 1. ...`).

### Runtime limit

The full notebook must execute in **under 120 seconds**.  If a computation takes longer, add a note and cache the result to a file.

### Execute before committing

```bash
uv run jupyter nbconvert --to notebook --execute notebooks/NN_<topic>.ipynb --inplace
```

Verify outputs: no empty plots, no NaN results, no unexpected warnings.  Commit the executed notebook (outputs included).

### Documentation link

After adding a notebook, update `docs/examples.md`:
- Add the notebook to the `nbgallery` directive.
- Add a `###` sub-section with a one-paragraph description.

Then verify the docs build: `uv run sphinx-build -W -E -b html docs docs/_build/html`.

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

## Versioning

STAMP uses [Semantic Versioning](https://semver.org/): **`MAJOR.MINOR.PATCH`**

| Part | Bump when |
|---|---|
| **MAJOR** | Backwards-incompatible API change — existing user code breaks |
| **MINOR** | New backwards-compatible functionality added |
| **PATCH** | Bug fix with no API change; internal refactor, docs, CI |

STAMP-specific mapping:

| Change | Bump |
|---|---|
| New public function added | MINOR |
| Bug fix to existing function | PATCH |
| Public function renamed, removed, or signature changed in breaking way | MAJOR |
| Internal refactor, docs, CI | PATCH |

Conventional Commits map directly: `feat:` → MINOR, `fix:` → PATCH, `feat!:` / `BREAKING CHANGE:` → MAJOR.

Start at `0.1.0`. The `0.x` range allows breaking changes without a MAJOR bump. Release `1.0.0` when the API is stable.

---

## Release process

Run all steps in order. **Do not tag until the PR is merged.**

### 1. Code quality
```bash
uv run ruff format .
uv run ruff check . --fix
uv run pytest --cov=stamp --cov-report=term-missing
```
All tests must pass, coverage must be ≥ 60%.

### 2. Check public API is complete
- Every public function has a NumPy docstring and at least one test.
- Any new module is importable.

```bash
uv run python -c "import stamp; print(dir(stamp))"
```

### 3. Run all notebooks end-to-end
```bash
uv run jupyter nbconvert --to notebook --execute notebooks/*.ipynb --inplace
```
Check outputs look correct — no empty plots, no NaN results, no unexpected warnings.

### 4. Build and verify docs
```bash
uv run sphinx-build -W -E -b html docs docs/_build/html
```
Fix any warnings before continuing. Open `docs/_build/html/index.html` and verify:
- sphinx-autoapi picked up all new modules
- `docs/examples.md` has a section for every notebook

### 5. Verify the build artifact
```bash
uv build
tar -tzf dist/nanoshot_stamp-*.tar.gz
```
Confirm no dev files (`CLAUDE.md`, `.github/`, `notebooks/`) appear in the sdist.

### 6. Update CHANGELOG
- Rename `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD`
- Add a fresh `[Unreleased]` section above it
- Entries must describe what users can *do*, not implementation details

### 7. Commit, PR, merge, THEN tag

**Never tag before the PR is merged** — tagging on a branch puts the version on a branch commit, not `main`, requiring extra cleanup PRs.

All release prep (CHANGELOG, last fixes) goes on the feature branch in the same PR.

```bash
# On the feature branch — commit everything and push
git add .
git commit -m "chore(release): bump version to vX.Y.Z"
git push
# → open PR, wait for CI, merge on GitHub

# After PR is merged:
git checkout main
git pull

# Tag the merge commit on main, push tag only
git tag vX.Y.Z
git push origin vX.Y.Z
```
Monitor the publish workflow at **Actions → Publish to PyPI**.

### 8. Verify the PyPI release
```bash
pip install nanoshot-stamp==X.Y.Z
python -c "import stamp; print(stamp.__version__)"
```
Run a quick smoke test of the main API paths to confirm the installed package works.

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
