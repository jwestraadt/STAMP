import os
import shutil
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "STAMP"
copyright = "2026, Johan Westraadt"
author = "Johan Westraadt"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "autoapi.extension",
    "myst_parser",
    "nbsphinx",
    "sphinx_design",
]

autoapi_dirs = ["../src"]
autoapi_type = "python"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]

napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

html_theme = "pydata_sphinx_theme"
html_title = "STAMP"

html_theme_options = {
    "logo": {
        "image_light": "_static/logo.svg",
        "image_dark": "_static/logo.svg",
        "text": "STAMP",
    },
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["navbar-icon-links"],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/jwestraadt/STAMP",
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        }
    ],
    "show_toc_level": 2,
    "navigation_with_keys": True,
    "use_edit_page_button": False,
}

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "notebooks/.ipynb_checkpoints"]

# Never re-execute notebooks during the docs build; use stored cell outputs.
nbsphinx_execute = "never"


def _sync_notebooks(app):
    """Copy repo-root notebooks/ into docs/notebooks/ so nbsphinx can find them."""
    confdir = os.path.dirname(os.path.abspath(__file__))
    src = os.path.normpath(os.path.join(confdir, "..", "notebooks"))
    dst = os.path.join(confdir, "notebooks")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def setup(app):
    app.connect("builder-inited", lambda app: _sync_notebooks(app))
