# Contributing to STAMP

Thank you for considering contributing to STAMP!

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/STAMP.git
   cd STAMP
   ```
3. Create a branch for your changes, using the Conventional Commits type as prefix:
   ```bash
   git checkout -b feat/your-feature-name    # new feature
   git checkout -b fix/module-short-desc     # bug fix
   git checkout -b docs/short-desc           # docs or notebooks
   git checkout -b chore/short-desc          # refactor, CI, maintenance
   ```

## Spec-driven development

All non-trivial features start with a written spec, approved before any code is written.

1. Copy `specs/_template.md` to `specs/<module>-<feature>.md` and fill it in — or run `/spec` in Claude Code to be interviewed through the questions one at a time.
2. Get the spec approved (comment on your issue or open a draft PR with just the spec file).
3. Once approved, implementation, tests, notebook, and docs all follow from the spec. The spec becomes the PR description.

See `specs/_template.md` for the full template and `CLAUDE.md` for the detailed workflow.

## Development Setup

STAMP uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies including dev extras
uv sync --all-extras
```

## Running Tests

```bash
uv run pytest
```

To run with coverage report:

```bash
uv run pytest --cov=stamp --cov-report=html
```

## Running the Linter

Check for lint errors:

```bash
uv run ruff check .
```

Check formatting:

```bash
uv run ruff format --check .
```

Auto-fix formatting:

```bash
uv run ruff format .
```

## Building the Docs

```bash
uv run sphinx-build docs docs/_build/html
```

Then open `docs/_build/html/index.html` in your browser.

## Submitting a Pull Request

1. Ensure all tests pass: `uv run pytest`
2. Ensure linting passes: `uv run ruff check . && uv run ruff format --check .`
3. Update `CHANGELOG.md` under `[Unreleased]`
4. Push your branch and open a pull request against `main` using **squash merge**
5. Use the approved spec as the PR description (summary, API block, behavioral requirements checklist)

## Code Style

- Code is formatted with [Ruff](https://docs.astral.sh/ruff/) (88-char lines)
- Use NumPy-style docstrings (mandatory — see CLAUDE.md for the full template)
- Type hints are encouraged

## Code of Conduct

Please be respectful and constructive in all interactions. We follow the
[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
