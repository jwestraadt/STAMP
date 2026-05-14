"""File I/O for loading microstructural feature measurements."""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from stamp._types import MeasurementData

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
) -> MeasurementData:
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
    MeasurementData
        Cleaned 1-D array of finite positive values with unit and label metadata.

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

    return MeasurementData(values=values, unit=unit, label=resolved_label)
