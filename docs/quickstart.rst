Quick Start
===========

Load data, apply stereological corrections, compute statistics, and plot — all in a few lines.

Loading measurements
--------------------

.. code-block:: python

   from stamp.io import load

   # Load grain areas from a CSV file (µm²)
   data = load("grains.csv", column="Area", unit="µm²", label="Grain Area")
   print(data.values[:5])  # numpy array of positive, finite values

Converting areas to diameters
------------------------------

.. code-block:: python

   from stamp.stereo import ecd_from_area

   ecds = ecd_from_area(data)   # unit becomes "µm", label becomes "ECD"

Descriptive statistics
----------------------

.. code-block:: python

   from stamp.stats import describe

   result = describe(ecds)
   print(f"n          : {result.n}")
   print(f"Arith. mean: {result.amean.mean:.2f} {ecds.unit}  "
         f"[{result.amean.ci_low:.2f}, {result.amean.ci_high:.2f}]")
   print(f"Geo. mean  : {result.gmean.mean:.2f} {ecds.unit}")
   print(f"Median     : {result.median.median:.2f} {ecds.unit}")
   print(f"Mode (KDE) : {result.peak.peak:.2f} {ecds.unit}")

Stereological correction (2-D → 3-D)
--------------------------------------

.. code-block:: python

   from stamp.stereo import saltykov, two_step

   # Saltykov/Wicksell unfolding
   sal = saltykov(ecds, n_bins=10)
   print(sal.bin_midpoints)   # 3-D bin centres
   print(sal.cdf_vol[-1])     # should be 100.0

   # Two-step lognormal fit (Lopez-Sanchez & Llana-Funez 2016)
   ts = two_step(ecds, bin_range=(10, 20))
   print(f"Geometric mean (3-D): {ts.geometric_mean:.2f} {ecds.unit}")
   print(f"Shape (mult. σ)     : {ts.shape:.3f}")

Plotting
--------

.. code-block:: python

   import matplotlib
   matplotlib.use("Agg")          # remove if running interactively

   from stamp.plot import distribution, saltykov_plot, twostep_plot

   fig1 = distribution(ecds, output_path="distribution.png")
   fig2 = saltykov_plot(sal,  output_path="saltykov.png")
   fig3 = twostep_plot(ts,    output_path="twostep.png")
