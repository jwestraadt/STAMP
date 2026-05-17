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


def _parse_phase_columns(columns: list[str]) -> dict[str, list[str]]:
    """Map each detected phase to its list of wide-format column names.

    Uses ``str.rsplit(' - ', 1)`` so that measurement names containing
    ' - ' (e.g. ``'Mean Intercept - Objects (Random) (um) - M23C6'``) are
    split correctly on the *rightmost* separator only.
    """
    phase_cols: dict[str, list[str]] = {}
    for col in columns:
        parts = col.rsplit(" - ", 1)
        if len(parts) == 2:
            phase = parts[1]
            phase_cols.setdefault(phase, []).append(col)
    return phase_cols


def load_mipar_image(
    path: str | Path,
    *,
    phases: list[str] | None = None,
    drop_columns: list[str] | None = None,
    rename_columns: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Load a MIPAR image-measurement CSV into a tidy long-format DataFrame.

    MIPAR image-measurement exports store one row per field-of-view (FOV).
    Each measurement column is named ``<MeasurementType> - <Phase>``.  This
    function auto-detects phases from column names and reshapes the table to
    long format with one row per (FOV × phase) combination.

    Parameters
    ----------
    path : str or Path
        Path to the MIPAR image-measurement CSV (or Excel) file.
    phases : list of str, optional
        Phases to retain.  ``None`` (default) keeps all auto-detected phases.
    drop_columns : list of str, optional
        Measurement column names to drop from the output after melting.
        Phase suffix must already be stripped (e.g. ``"Area Fraction (%)"``).
    rename_columns : dict of {str: str}, optional
        Rename map applied to measurement columns after melting, e.g.
        ``{"Area Fraction (%)": "Vv (%)"}``.

    Returns
    -------
    pd.DataFrame
        Long-format table with columns ``Image``, ``Phase``, and one column
        per measurement type (phase suffix stripped).  Row count equals
        ``n_FOVs × n_phases`` before any *phases* filter.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the file extension is unsupported, the file is empty, the
        ``Image`` column is absent, any entry in *phases* is not found in the
        file, or any entry in *drop_columns* is not present in the output.

    Examples
    --------
    >>> df = load_mipar_image("GOO220_52_BatchMeas.csv")
    >>> df["Phase"].unique()
    array(['M23C6', 'MX ZPhase', 'Laves'], dtype=object)
    >>> df.shape
    (30, 16)
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
        df = pd.read_csv(path, sep=sep, engine="python", index_col=False)
        df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    else:
        df = pd.read_excel(path)

    if df.empty:
        raise ValueError(f"File is empty (no data rows): {path}")

    if "Image" not in df.columns:
        raise ValueError(
            f"Required column 'Image' not found. Available columns: {list(df.columns)}"
        )

    measurement_cols = [c for c in df.columns if c != "Image"]
    phase_cols = _parse_phase_columns(measurement_cols)

    if phases is not None:
        unknown = [p for p in phases if p not in phase_cols]
        if unknown:
            raise ValueError(
                f"Phase(s) not found in file: {unknown}. "
                f"Detected phases: {sorted(phase_cols)}."
            )

    frames = []
    for phase, cols in phase_cols.items():
        sub = df[["Image"] + cols].copy()
        sub.columns = pd.Index(["Image"] + [c.rsplit(" - ", 1)[0] for c in cols])
        sub.insert(1, "Phase", phase)
        frames.append(sub)

    result = pd.concat(frames, ignore_index=True)

    if phases is not None:
        result = result[result["Phase"].isin(phases)].reset_index(drop=True)

    if drop_columns is not None:
        meas_cols_out = [c for c in result.columns if c not in ("Image", "Phase")]
        missing = [c for c in drop_columns if c not in meas_cols_out]
        if missing:
            raise ValueError(
                f"Column(s) not found in melted DataFrame: {missing}. "
                f"Available measurement columns: {sorted(meas_cols_out)}."
            )
        result = result.drop(columns=drop_columns)

    if rename_columns is not None:
        result = result.rename(columns=rename_columns)

    return result


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
