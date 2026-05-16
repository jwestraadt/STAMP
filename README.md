<div align="center">
<img src="docs/_static/logo.svg" alt="STAMP logo" width="120"/>

# STAMP

[![CI](https://github.com/jwestraadt/STAMP/actions/workflows/ci.yml/badge.svg)](https://github.com/jwestraadt/STAMP/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/nanoshot-stamp)](https://pypi.org/project/nanoshot-stamp/)
[![Python versions](https://img.shields.io/pypi/pyversions/nanoshot-stamp)](https://pypi.org/project/nanoshot-stamp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![codecov](https://codecov.io/gh/jwestraadt/STAMP/branch/main/graph/badge.svg)](https://codecov.io/gh/jwestraadt/STAMP)

**Stereological Tools for Analysis of Microstructural Parameters**
</div>

STAMP is a scientific Python package for quantitative 2-D microstructural analysis.
It provides tools to load grain or precipitate measurements, apply stereological
corrections to recover 3-D size distributions, compute descriptive statistics with
confidence intervals, and generate publication-ready figures.

## Modules

| Module | Purpose |
|---|---|
| `stamp.io` | Load CSV, Excel, or TXT/TSV files and MIPAR feature-measurement exports into a `pd.DataFrame` |
| `stamp.stereo` | Stereological corrections: ECD conversion, Fullman (1953) linear intercept, Saltykov/Wicksell (1925/1967) matrix unfolding, two-step lognormal fitting (Lopez-Sanchez & Llana-Funez 2016) |
| `stamp.stats` | Descriptive statistics with confidence intervals: arithmetic mean (ASTM E112, GCI, mCox), geometric mean (CLT, Bayesian), median (Hollander–Wolfe), KDE mode, MLE distribution fitting with KS goodness-of-fit |
| `stamp.plot` | Publication-ready figures: histogram + KDE, Saltykov dual-panel (frequency + volume CDF), two-step fit with ±3σ band, PDF/CDF profile, Q-Q plot |
| `stamp.pipeline` | Batch processing across multiple material states; produces a `PipelineResult` with per-state statistics, a summary DataFrame, and optional auto-saved box plot and CSV |

## Installation

```bash
pip install nanoshot-stamp
```

To also install JupyterLab for running the example notebooks:

```bash
pip install "nanoshot-stamp[notebooks]"
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add "nanoshot-stamp[notebooks]"
```

## Documentation

Full documentation is available at [stamp.readthedocs.io](https://stamp.readthedocs.io/).

## Citation

If you use STAMP in your research, please cite it:

```bibtex
@software{westraadt_stamp_2026,
  author  = {Westraadt, Johan},
  title   = {STAMP: Stereological Tools for Analysis of Microstructural Parameters},
  year    = {2026},
  url     = {https://github.com/jwestraadt/STAMP},
  license = {MIT}
}
```

Or use GitHub's **Cite this repository** button (powered by [CITATION.cff](CITATION.cff)).

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT — see [LICENSE](LICENSE) for details.
