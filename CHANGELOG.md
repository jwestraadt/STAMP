# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

**Notebooks**
- `04_mipar_feature_analysis` and `05_mipar_image_analysis` — updated to
  reflect a 4-phase MIPAR segmentation where `MX ZPhase` is split into two
  independent phases (`MX` and `ZPhase`); `FILES` and `STATE_LABELS` trimmed
  to the three available material states (GOO220\_51 gauge, \_52 thread,
  \_53 fracture)
- `run_mipar` pipeline gains `phase_aliases` and `missing_phase` parameters
  so notebooks can normalise phase name capitalisation variants and handle
  states where a phase is absent without raising an error

### Fixed

**Notebooks**
- Corrected mojibake in `05_mipar_image_analysis` (axis labels, print
  statements, and LaTeX captions displayed garbled characters such as
  `â€"` and `Âµ` instead of `—` and `µ`)

## [0.1.0a5] - 2026-05-17

### Added

**Stereology**
- Derive volume fraction ($V_V$), surface area density ($S_V$), mean caliper
  diameter ($\bar{D}$), and 3-D mean free path ($\lambda_{3D}$) from MIPAR
  image-level measurements — applies Delesse (1848), Underwood (1970), and
  Fullman (1953) relations directly to per-FOV DataFrame columns
  (`stamp.stereo.volume_fraction`, `surface_area_density`,
  `mean_caliper_diameter`, `mean_free_path_3d`)

**I/O**
- Load MIPAR image-measurement batch CSVs (one row per FOV, all phases as
  column suffixes) into a tidy long-format DataFrame with one row per
  (FOV × phase) combination (`stamp.io.load_mipar_image()`)

**Export**
- Publication-ready figure styling and table export — apply journal formatting
  (default, Nature preset, or custom overrides) to any STAMP plot and export
  results tables as CSV or LaTeX booktabs (`stamp.export`)

**Notebooks**
- `05_mipar_image_analysis` — new notebook demonstrating `load_mipar_image`
  across three material states; derives and compares 2-D quantities (phase
  fraction, mean particle size, interparticle spacing) and 3-D stereological
  quantities ($V_V$, $S_V$, $\bar{D}$, $\lambda_{3D}$) per phase with
  Nature journal-style box plots and LaTeX table exports
- `04_mipar_feature_analysis` — plots converted to Nature journal style (B&W,
  hatch-differentiated boxes, correct column widths); summary table now also
  exported as a LaTeX booktabs file via `stamp.export.to_latex`

## [0.1.0a4] - 2026-05-16

### Added
- Install JupyterLab and ipykernel alongside STAMP with `pip install "nanoshot-stamp[notebooks]"`

### Fixed
- Minor development and packaging fixes

## [0.1.0a2] - 2026-05-16

### Added
- Optional `notebooks` extra — installs JupyterLab and ipykernel for running the example notebooks (`pip install "nanoshot-stamp[notebooks]"`)

## [0.1.0a1] - 2026-05-16

### Added

**Pipeline**
- Multi-state scripted analysis pipeline — run the full load → statistics workflow across any number of material states (heat treatments, compositions, processing routes, etc.), each with multiple fields-of-view (`stamp.pipeline.run()`)
- Side-by-side box plot comparing per-field-of-view mean statistics across all material states, with individual data points overlaid (`stamp.pipeline.boxplot()`)
- Export the per-field-of-view summary table (arithmetic mean, geometric mean, median, CIs, percentiles) to CSV (`stamp.pipeline.export_csv()`)
- Run the full pipeline directly on MIPAR feature-measurement CSVs — groups rows by image/FOV, filters to a chosen precipitate phase, and returns the same `PipelineResult` as `run()` (`stamp.pipeline.run_mipar()`)

**I/O**
- Load grain measurements from CSV, Excel (.xlsx/.xls), or plain-text files — `stamp.io.load()` now returns a single-column `pd.DataFrame` with physical unit and label stored in `df.attrs`, making the loading API consistent with `load_mipar_features()`
- Load a MIPAR feature-measurement CSV into a pandas DataFrame for custom filtering and inspection (`stamp.io.load_mipar_features()`)

**Stereology**
- Convert 2-D projected areas to equivalent circle diameters (`stamp.stereo.ecd_from_area()`)
- Fullman (1953) linear intercept correction for 2-D → 3-D mean grain diameter (`stamp.stereo.linear_intercept_correction()`)
- Saltykov/Wicksell matrix unfolding — recovers the 3-D sphere-diameter frequency distribution from 2-D circle measurements, including a volume-weighted CDF (`stamp.stereo.saltykov()`)
- Two-step lognormal fit (Lopez-Sanchez & Llana-Funez 2016) — iterates Saltykov over a range of bin counts and returns the best-fit geometric mean and log-shape σ with a ±3σ uncertainty band (`stamp.stereo.two_step()`)

**Statistics**
- Arithmetic mean with ASTM, GCI, and mCox confidence intervals (`stamp.stats.amean()`)
- Geometric mean with CLT and Bayesian confidence intervals (`stamp.stats.gmean()`)
- Median with IQR and Hollander–Wolfe confidence interval (`stamp.stats.median()`)
- KDE mode estimation with Silverman, Scott, or user-supplied bandwidth (`stamp.stats.freq_peak()`)
- MLE distribution fitting for normal and lognormal with KS goodness-of-fit test (`stamp.stats.fit()`)
- Single-call summary of all descriptive statistics (`stamp.stats.describe()`)

**Plots**
- Histogram + KDE with annotated averages and optional fitted distribution overlay (`stamp.plot.distribution()`)
- Dual-panel 3-D frequency and volume-weighted CDF figure for Saltykov results (`stamp.plot.saltykov_plot()`)
- Lognormal fit curve with ±3σ uncertainty band for two-step results (`stamp.plot.twostep_plot()`)
- PDF or empirical CDF profile (`stamp.plot.distribution_profile()`)
- Quantile-quantile plot against normal or lognormal reference (`stamp.plot.qq_plot()`)
- Dual-panel comparison of 2-D apparent vs corrected 3-D distributions with recovery error annotation (`stamp.plot.comparison_plot()`)

**Simulation**
- Monte Carlo Wicksell corpuscle simulation — generates a synthetic lognormal or normal 3-D grain population and random 2-D cross-sections for validating stereological corrections (`stamp.simulate.simulate_section()`)

**Notebooks**
- `notebooks/01_quickstart.ipynb` — end-to-end workflow: load measurements, compute statistics, apply Saltykov and two-step corrections, generate all plots
- `notebooks/02_simulation_validation.ipynb` — Monte Carlo validation of stereological corrections including Wicksell bias demo, recovery accuracy table, and sample-size sweep

**Documentation**
- Added STAMP logo (stylised grain-boundary pattern) shown in the docs navbar and README
- Switched documentation theme to PyData Sphinx Theme with a top navigation bar (Installation, Examples, Contributing, Changelog, API Reference) and GitHub link

[Unreleased]: https://github.com/jwestraadt/STAMP/compare/v0.1.0a5...HEAD
[0.1.0a5]: https://github.com/jwestraadt/STAMP/compare/v0.1.0a4...v0.1.0a5
[0.1.0a4]: https://github.com/jwestraadt/STAMP/compare/v0.1.0a3...v0.1.0a4
[0.1.0a2]: https://github.com/jwestraadt/STAMP/compare/v0.1.0a1...v0.1.0a2
[0.1.0a1]: https://github.com/jwestraadt/STAMP/releases/tag/v0.1.0a1
