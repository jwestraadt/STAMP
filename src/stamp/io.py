"""File I/O for loading microstructural feature measurements."""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

_TEXT_EXTENSIONS = {".csv", ".txt", ".tsv"}
_EXCEL_EXTENSIONS = {".xlsx", ".xls"}
_ALL_EXTENSIONS = _TEXT_EXTENSIONS | _EXCEL_EXTENSIONS


def load(
    path: str | Path,
    column: str | int,
    unit: str,
    label: str | None = None,
    delimiter: str | None = None,
    skip_rows: int = 0,
    sheet_name: str | int = 0,
) -> pd.DataFrame:
    """Load a column of positive measurements from a delimited text or Excel file.

    Parameters
    ----------
    path : str or Path
        Path to a ``.csv``, ``.txt``, ``.tsv``, ``.xlsx``, or ``.xls`` file.
    column : str or int
        Column name (str) or 0-based column index (int).
    unit : str
        Physical unit string, e.g. ``"µm"`` or ``"µm²"``.
    label : str, optional
        Display label.  Defaults to the column name when *column* is a str,
        otherwise ``"Feature"``.
    delimiter : str, optional
        Field separator for text files.  Auto-detected by pandas when ``None``.
    skip_rows : int, optional
        Number of leading rows to skip before the header row.  Default 0.
    sheet_name : str or int, optional
        Excel sheet name or 0-based index.  Ignored for text files.  Default 0.

    Returns
    -------
    pd.DataFrame
        Single-column DataFrame of cleaned finite positive values.  The column
        is named after *label*.  Two metadata keys are set in ``df.attrs``:
        ``"unit"`` (the physical unit string) and ``"label"`` (the display
        label).

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the file extension is unsupported, *column* is not found, or no
        finite positive values remain after cleaning.

    Notes
    -----
    Non-finite values (NaN, ±inf) and values ≤ 0 are silently dropped; a
    :func:`warnings.warn` states the number of removed rows.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext not in _ALL_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension {ext!r}. "
            f"Supported extensions: {sorted(_ALL_EXTENSIONS)}"
        )

    if ext in _TEXT_EXTENSIONS:
        if delimiter is not None:
            sep = delimiter
        elif ext == ".csv":
            sep = ","
        elif ext == ".tsv":
            sep = "\t"
        else:
            # .txt: match any whitespace so tab/space files both work
            sep = r"\s+"
        df = pd.read_csv(path, sep=sep, skiprows=skip_rows, engine="python")
    else:
        df = pd.read_excel(path, sheet_name=sheet_name, skiprows=skip_rows)

    if isinstance(column, str):
        if column not in df.columns:
            raise ValueError(
                f"Column {column!r} not found. Available columns: {list(df.columns)}"
            )
        series = df[column]
        resolved_label = label if label is not None else column
    else:
        if column >= len(df.columns):
            raise ValueError(
                f"Column index {column} out of range "
                f"(DataFrame has {len(df.columns)} column(s))."
            )
        series = df.iloc[:, column]
        resolved_label = label if label is not None else "Feature"

    values = pd.to_numeric(series, errors="coerce").to_numpy(
        dtype=np.float64, na_value=np.nan
    )

    bad_mask = ~np.isfinite(values) | (values <= 0)
    n_bad = int(bad_mask.sum())
    if n_bad > 0:
        warnings.warn(
            f"Dropped {n_bad} row(s) with non-finite or non-positive values.",
            UserWarning,
            stacklevel=2,
        )
    values = values[~bad_mask]

    if len(values) == 0:
        raise ValueError("No valid (finite, positive) values remain after cleaning.")

    out = pd.DataFrame({resolved_label: values})
    out.attrs["unit"] = unit
    out.attrs["label"] = resolved_label
    return out


def load_mipar_features(
    path: str | Path,
    *,
    image_col: str = "Image",
    phase_col: str = "Layer",
) -> pd.DataFrame:
    """Load a MIPAR feature-measurement CSV into a pandas DataFrame.

    MIPAR (Material Image Processing and Reconstruction) exports a single CSV
    file per material state.  Each row is one measured feature (e.g. a
    precipitate particle).  The file contains at least an image/FOV column,
    a phase/layer column, and one or more measurement columns.

    Parameters
    ----------
    path : str or Path
        Path to the MIPAR CSV (or Excel) file.
    image_col : str, optional
        Name of the column identifying the field-of-view image.
        Default ``"Image"``.
    phase_col : str, optional
        Name of the column identifying the precipitate phase or layer.
        Default ``"Layer"``.

    Returns
    -------
    pd.DataFrame
        Full data table with all columns as exported by MIPAR.  The
        *image_col* and *phase_col* columns are cast to ``str``; all other
        columns are left as-is.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the file extension is unsupported, or *image_col* / *phase_col*
        are not present in the file.

    Examples
    --------
    >>> df = load_mipar_features("FeatureMeas.csv")
    >>> df["Layer"].unique()
    array(['M23C6', 'MX ZPhase', 'Laves'], dtype=object)
    >>> df.groupby("Layer")["Equivalent Diameter (um)"].describe()
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext not in _ALL_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension {ext!r}. "
            f"Supported extensions: {sorted(_ALL_EXTENSIONS)}"
        )

    if ext in _TEXT_EXTENSIONS:
        sep = "\t" if ext == ".tsv" else ","
        # index_col=False prevents column-shift when MIPAR appends a trailing
        # comma to every data row (giving one more field than the header row).
        df = pd.read_csv(path, sep=sep, engine="python", index_col=False)
        # Drop the phantom empty column produced by the trailing comma.
        df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    else:
        df = pd.read_excel(path)

    missing = [c for c in (image_col, phase_col) if c not in df.columns]
    if missing:
        raise ValueError(
            f"Required column(s) {missing} not found. "
            f"Available columns: {list(df.columns)}"
        )

    df[image_col] = df[image_col].astype(str)
    df[phase_col] = df[phase_col].astype(str)
    return df
