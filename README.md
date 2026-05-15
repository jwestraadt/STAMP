# STAMP

[![CI](https://github.com/jwestraadt/STAMP/actions/workflows/ci.yml/badge.svg)](https://github.com/jwestraadt/STAMP/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/stamp)](https://pypi.org/project/stamp/)
[![Python versions](https://img.shields.io/pypi/pyversions/stamp)](https://pypi.org/project/stamp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![codecov](https://codecov.io/gh/jwestraadt/STAMP/branch/main/graph/badge.svg)](https://codecov.io/gh/jwestraadt/STAMP)

**Stereological Tools for Analysis of Microstructural Parameters**

STAMP is a scientific Python package for quantitative 2-D microstructural analysis.
It provides tools to load grain or precipitate measurements, apply stereological
corrections to recover 3-D size distributions, compute descriptive statistics with
confidence intervals, and generate publication-ready figures.

## Features

- **I/O** — load CSV, Excel, TXT/TSV files into a validated `MeasurementData` container; non-finite and non-positive values are dropped with a warning
- **Stereology** — ECD conversion, Fullman (1953) linear intercept correction, Saltykov/Wicksell (1925/1967) matrix unfolding, Two-step lognormal fitting (Lopez-Sanchez & Llana-Funez 2016)
- **Statistics** — arithmetic mean (ASTM E112, GCI, mCox), geometric mean (CLT, Bayesian), median (Hollander–Wolfe CI), KDE mode, MLE distribution fitting with KS goodness-of-fit
- **Plots** — histogram + KDE, Saltykov dual-panel (frequency + volume CDF), two-step fit with ±3σ band, PDF/CDF profile, Q-Q plot; all figures return a `matplotlib.Figure` and optionally save to file

## Installation

```bash
pip install stamp
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add stamp
```

## Documentation

Full documentation is available at [jwestraadt.github.io/STAMP](https://jwestraadt.github.io/STAMP).

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
