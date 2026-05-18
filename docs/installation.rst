Installation
============

From PyPI
---------

.. code-block:: bash

   pip install nanoshot-stamp

To also install JupyterLab for running the example notebooks:

.. code-block:: bash

   pip install "nanoshot-stamp[notebooks]"

With `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: bash

   uv add nanoshot-stamp

   # with Jupyter extras
   uv add "nanoshot-stamp[notebooks]"

From Source
-----------

.. code-block:: bash

   git clone https://github.com/jwestraadt/STAMP.git
   cd STAMP
   uv sync --all-extras

Requirements
------------

- Python 3.9 or later
