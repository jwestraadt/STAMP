STAMP Documentation
===================

**Stereological Tools for Analysis of Microstructural Parameters**

STAMP is a scientific Python package for quantitative 2-D microstructural analysis.
It provides tools to load grain or precipitate measurements, apply stereological
corrections to recover 3-D size distributions, compute descriptive statistics with
confidence intervals, and generate publication-ready figures.

----

Installation
------------

.. tab-set::

   .. tab-item:: pip

      .. code-block:: bash

         pip install nanoshot-stamp

   .. tab-item:: uv

      .. code-block:: bash

         uv add nanoshot-stamp

   .. tab-item:: With Jupyter

      .. code-block:: bash

         pip install "nanoshot-stamp[notebooks]"

      Or with uv:

      .. code-block:: bash

         uv add "nanoshot-stamp[notebooks]"

See :doc:`installation` for full details including building from source.

----

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Examples
      :link: examples
      :link-type: doc

      Jupyter notebooks walking through the core STAMP workflow — loading
      measurements, applying stereological corrections, computing statistics,
      and generating publication-ready figures.

   .. grid-item-card:: API Reference
      :link: autoapi/stamp/index
      :link-type: doc

      Full documentation for all public functions and parameters across
      ``stamp.io``, ``stamp.stereo``, ``stamp.stats``, ``stamp.plot``,
      and ``stamp.pipeline``.

   .. grid-item-card:: Installation
      :link: installation
      :link-type: doc

      Detailed installation instructions including optional extras and
      building from source.

   .. grid-item-card:: Contributing
      :link: contributing
      :link-type: doc

      How to contribute — spec-driven development workflow, commit
      conventions, and the pre-commit checklist.

----

Citing STAMP
------------

If you use STAMP in your research, please cite it:

.. code-block:: bibtex

   @software{westraadt_stamp_2026,
     author  = {Westraadt, Johan},
     title   = {STAMP: Stereological Tools for Analysis of Microstructural Parameters},
     year    = {2026},
     url     = {https://github.com/jwestraadt/STAMP},
     license = {MIT}
   }

Or use the **Cite this repository** button on GitHub (powered by
`CITATION.cff <https://github.com/jwestraadt/STAMP/blob/main/CITATION.cff>`_).

----

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: User guide

   installation
   examples

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Reference

   autoapi/index

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Development

   contributing
   changelog
