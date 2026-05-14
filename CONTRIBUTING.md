# Contributing to STAMP

Thank you for considering contributing to STAMP!

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/STAMP.git
   cd STAMP
   ```
3. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

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
4. Push your branch and open a pull request against `main`
5. Describe what your PR does and reference any related issues

## Code Style

- Code is formatted with [Ruff](https://docs.astral.sh/ruff/) (88-char lines)
- Use NumPy-style or Google-style docstrings
- Type hints are encouraged

## Code of Conduct

Please be respectful and constructive in all interactions. We follow the
[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
