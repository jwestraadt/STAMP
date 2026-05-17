# Examples

The notebooks below walk through the core STAMP workflow, validate stereological
corrections, demonstrate the multi-state pipeline, and show MIPAR feature-measurement
analysis.  Run them interactively with `uv run jupyter lab`.

## Loading data

`stamp.io.load` returns a single-column `pd.DataFrame`.  The physical unit and
display label are stored in `df.attrs["unit"]` and `df.attrs["label"]`.
All `stamp.stats`, `stamp.stereo`, and `stamp.plot` functions accept this
DataFrame directly — no manual unpacking needed:

```python
from stamp.io import load
from stamp.stats import describe
from stamp.stereo import saltykov, two_step
from stamp.plot import distribution

ecds = load("grains.csv", column="ECD_um", unit="µm", label="Grain ECD")

stats  = describe(ecds)          # pd.DataFrame accepted directly
sal    = saltykov(ecds, n_bins=12)
ts     = two_step(ecds)
fig    = distribution(ecds)
```

`stamp.io.load_mipar_features` also returns a `pd.DataFrame` (with all MIPAR
columns preserved).  The `stamp.pipeline` functions (`run`, `run_batch`,
`run_mipar`) handle loading and type-conversion internally.

## Notebooks

```{nbgallery}
notebooks/01_quickstart
notebooks/02_simulation_validation
notebooks/03_multi_state_pipeline
notebooks/04_mipar_feature_analysis
notebooks/05_mipar_image_analysis
```

### Quick Start

**`01_quickstart.ipynb`** — end-to-end workflow for a single material state:
load measurements from a text file, compute descriptive statistics with
confidence intervals, fit a lognormal distribution, apply Saltykov / two-step
stereological correction, generate publication-ready figures, and export results
tables as CSV or LaTeX using `stamp.export` (§9 demonstrates default, Nature,
and custom journal styles).

### Stereological Correction Validation

**`02_simulation_validation.ipynb`** — Monte Carlo Wicksell validation: simulate
a synthetic lognormal 3-D grain population, generate 2-D cross-sections, apply
Saltykov and two-step corrections, and quantify recovery accuracy across a range
of sample sizes and bin counts.

### Multi-State Pipeline

**`03_multi_state_pipeline.ipynb`** — `stamp.pipeline.run_batch` applied to three
heat-treatment states stored as single batch CSV files.  Demonstrates apparent (2-D)
vs stereologically corrected (3-D) geometric means side-by-side with ground-truth
reference lines.

### MIPAR Feature Measurement Analysis

**`04_mipar_feature_analysis.ipynb`** — `stamp.pipeline.run_mipar` applied to
MIPAR feature-measurement CSVs containing multiple precipitate phases (M23C6,
MX ZPhase, Laves) across two material states (GOO220\_52 vs GOO220\_53).  Shows
per-FOV ECD box plots for each phase rendered in Nature journal style (B&W,
hatch-differentiated boxes, 89 mm / 180 mm column widths) and exports the
summary statistics table as both CSV and a LaTeX booktabs table via
`stamp.export.to_latex`.

### MIPAR Image-Level Measurement Analysis

**`05_mipar_image_analysis.ipynb`** — `stamp.io.load_mipar_image` applied to
MIPAR batch image-measurement CSVs (one row per FOV, all phases as column
suffixes) across three material states (GOO220\_51, GOO220\_52, GOO220\_53).
Demonstrates auto-detection of phases, long-format reshaping, and two
analysis tiers: (1) 2-D per-FOV quantities — phase fraction, mean particle
size, and interparticle spacing — summarised and plotted in Nature journal
style; (2) 3-D stereological quantities — volume fraction $V_V$, surface
area density $S_V$, mean caliper diameter $\bar{D}$, and 3-D mean free path
$\lambda_{3D}$ — derived using `stamp.stereo.volume_fraction`,
`surface_area_density`, `mean_caliper_diameter`, and `mean_free_path_3d`,
then summarised and plotted in the same style.  All tables exported as CSV
and LaTeX booktabs via `stamp.export`.
