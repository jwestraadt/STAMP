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

## Quick Start

```python
import numpy as np
from stamp.io import load
from stamp.stereo import ecd_from_area, saltykov, two_step
from stamp.stats import describe
from stamp.plot import distribution, saltykov_plot, twostep_plot

# Load grain areas from a CSV file
data = load("grains.csv", column="Area", unit="µm²", label="Grain Area")

# Convert 2-D projected areas to equivalent circle diameters
ecds = ecd_from_area(data)

# Descriptive statistics with 95 % confidence intervals
result = describe(ecds)
print(f"Arithmetic mean : {result.amean.mean:.2f} µm  "
      f"[{result.amean.ci_low:.2f}, {result.amean.ci_high:.2f}]")
print(f"Geometric mean  : {result.gmean.mean:.2f} µm")
print(f"Median          : {result.median.median:.2f} µm")

# Saltykov/Wicksell stereological correction (2-D → 3-D)
sal = saltykov(ecds, n_bins=10)

# Two-step lognormal fit
ts = two_step(ecds, bin_range=(10, 20))
print(f"3-D geometric mean: {ts.geometric_mean:.2f} µm")

# Publication-ready plots (saved to PNG, 300 dpi)
distribution(ecds, output_path="distribution.png")
saltykov_plot(sal,  output_path="saltykov.png")
twostep_plot(ts,    output_path="twostep.png")
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
