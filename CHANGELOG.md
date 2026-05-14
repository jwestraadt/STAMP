# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `stamp.simulate.simulate_section()` — Monte Carlo Wicksell corpuscle simulation: generates a synthetic lognormal or normal 3-D grain pool and random 2-D cross-sections with configurable sample size and seed
- `SimulationResult` dataclass in `stamp._types`, re-exported from `stamp`
- `stamp.plot.comparison_plot()` — dual-panel validation figure comparing 2-D apparent vs true 3-D and Saltykov/two-step corrected distributions with geometric mean annotation and recovery error
- `notebooks/01_quickstart.ipynb` — end-to-end quick start: load CSV, ECD conversion, descriptive stats, Saltykov, two-step, and all plots
- `notebooks/02_simulation_validation.ipynb` — Monte Carlo validation of stereological corrections; includes Wicksell bias demo, recovery accuracy table, and sample-size sweep
- `jupyterlab>=4.0` added to dev dependency group
- Initial project scaffold
- `stamp._types` — shared dataclasses (`MeasurementData`, `SaltykovResult`, `TwoStepResult`, `MeanResult`, `MedianResult`, `PeakResult`, `FitResult`, `DescribeResult`) re-exported from `stamp`
- `stamp.io.load()` — reads CSV, Excel, TXT/TSV files into `MeasurementData`; drops non-finite/non-positive rows with a warning
- `stamp.stereo.ecd_from_area()` — converts 2-D areas to equivalent circle diameters
- `stamp.stereo.linear_intercept_correction()` — Fullman (1953) 2-D → 3-D grain diameter correction
- `stamp.stereo.saltykov()` — Saltykov/Wicksell matrix unfolding with volume-weighted CDF
- `stamp.stereo.two_step()` — Lopez-Sanchez & Llana-Funez (2016) iterative lognormal fitting with ±3σ uncertainty band
- `stamp.stats.amean()` — arithmetic mean with ASTM, GCI, and mCox confidence intervals
- `stamp.stats.gmean()` — geometric mean with CLT and Bayesian confidence intervals
- `stamp.stats.median()` — median with IQR and Hollander–Wolfe confidence interval
- `stamp.stats.freq_peak()` — KDE mode estimation (Silverman, Scott, or scalar bandwidth)
- `stamp.stats.fit()` — MLE distribution fitting for normal and lognormal with KS goodness-of-fit
- `stamp.stats.describe()` — convenience wrapper returning all statistics in one result
- `stamp.plot.distribution()` — histogram + KDE with annotated averages and optional fit overlay
- `stamp.plot.saltykov_plot()` — dual-panel 3-D frequency and volume-weighted CDF figure
- `stamp.plot.twostep_plot()` — lognormal fit curve with ±3σ uncertainty band
- `stamp.plot.distribution_profile()` — PDF or empirical CDF profile
- `stamp.plot.qq_plot()` — quantile-quantile plot against normal or lognormal distribution
- 141 tests across all modules; 97 % line coverage

### Changed
- `README.md` — rewrote with full project description, feature list, and working Quick Start example using the real API
- `docs/quickstart.rst` — replaced placeholder with a complete worked example (load → ECD → stats → Saltykov → two-step → plots)
- `pyproject.toml` — updated package description to "Stereological Tools for Analysis of Microstructural Parameters"

### Fixed
- `docs/api.rst` — replaced removed `.. autoapi-index::` directive (incompatible with sphinx-autoapi v3) with a prose reference to the auto-generated `autoapi/index`

[Unreleased]: https://github.com/jwestraadt/STAMP/compare/HEAD...HEAD
