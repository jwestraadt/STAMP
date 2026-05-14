"""Tests for stamp.io.load."""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stamp._types import MeasurementData
from stamp.io import load

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_csv(path: Path, data: dict) -> Path:
    pd.DataFrame(data).to_csv(path, index=False)
    return path


def _write_excel(path: Path, data: dict) -> None:
    pd.DataFrame(data).to_excel(path, index=False)


def _write_txt(path: Path, data: dict, sep: str = "\t") -> Path:
    pd.DataFrame(data).to_csv(path, index=False, sep=sep)
    return path


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


def test_load_csv_by_name(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"ecd": [1.0, 2.0, 3.0]})
    result = load(p, column="ecd", unit="µm")
    assert isinstance(result, MeasurementData)
    np.testing.assert_array_equal(result.values, [1.0, 2.0, 3.0])
    assert result.unit == "µm"
    assert result.label == "ecd"


def test_load_csv_by_index(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"ecd": [1.0, 2.0], "area": [4.0, 5.0]})
    result = load(p, column=1, unit="µm²", label="Grain Area")
    np.testing.assert_array_equal(result.values, [4.0, 5.0])
    assert result.label == "Grain Area"


def test_load_txt_tab_delimited(tmp_path):
    p = _write_txt(tmp_path / "data.txt", {"size": [10.0, 20.0, 30.0]})
    result = load(p, column="size", unit="µm")
    np.testing.assert_array_equal(result.values, [10.0, 20.0, 30.0])


def test_load_tsv(tmp_path):
    p = _write_txt(tmp_path / "data.tsv", {"d": [5.0, 6.0]})
    result = load(p, column="d", unit="µm")
    np.testing.assert_array_equal(result.values, [5.0, 6.0])


def test_load_excel(tmp_path):
    p = tmp_path / "data.xlsx"
    _write_excel(p, {"grain": [2.5, 3.5, 4.5]})
    result = load(p, column="grain", unit="µm")
    np.testing.assert_array_almost_equal(result.values, [2.5, 3.5, 4.5])


def test_label_defaults_to_column_name(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"diameter": [1.0]})
    result = load(p, column="diameter", unit="µm")
    assert result.label == "diameter"


def test_label_defaults_to_feature_for_int_column(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"diameter": [1.0]})
    result = load(p, column=0, unit="µm")
    assert result.label == "Feature"


def test_values_are_float64(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"x": [1, 2, 3]})
    result = load(p, column="x", unit="µm")
    assert result.values.dtype == np.float64


def test_skip_rows(tmp_path):
    # Write a file with one extra header row before the real header
    content = "metadata line\necd\n1.0\n2.0\n3.0\n"
    p = tmp_path / "data.csv"
    p.write_text(content)
    result = load(p, column="ecd", unit="µm", skip_rows=1)
    np.testing.assert_array_equal(result.values, [1.0, 2.0, 3.0])


# ---------------------------------------------------------------------------
# Data-cleaning behaviour
# ---------------------------------------------------------------------------


def test_nan_values_dropped_with_warning(tmp_path):
    # Write a non-numeric entry; pd.to_numeric(errors='coerce') converts it to NaN.
    p = tmp_path / "data.csv"
    p.write_text("x\n1.0\nnot_a_number\n3.0\n")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = load(p, column="x", unit="µm")
    user_warns = [x for x in w if issubclass(x.category, UserWarning)]
    assert len(user_warns) == 1
    assert "Dropped 1" in str(user_warns[0].message)
    np.testing.assert_array_equal(result.values, [1.0, 3.0])


def test_negative_values_dropped_with_warning(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"x": [1.0, -2.0, 3.0]})
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = load(p, column="x", unit="µm")
    assert len(w) == 1
    np.testing.assert_array_equal(result.values, [1.0, 3.0])


def test_zero_values_dropped_with_warning(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"x": [0.0, 1.0, 2.0]})
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = load(p, column="x", unit="µm")
    assert len(w) == 1
    np.testing.assert_array_equal(result.values, [1.0, 2.0])


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        load("/nonexistent/path/data.csv", column="x", unit="µm")


def test_unsupported_extension_raises(tmp_path):
    p = tmp_path / "data.hdf5"
    p.write_text("")
    with pytest.raises(ValueError, match="Unsupported"):
        load(p, column="x", unit="µm")


def test_column_name_not_found_raises(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"x": [1.0]})
    with pytest.raises(ValueError, match="not found"):
        load(p, column="y", unit="µm")


def test_column_index_out_of_range_raises(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"x": [1.0]})
    with pytest.raises(ValueError, match="out of range"):
        load(p, column=5, unit="µm")


def test_no_valid_values_raises(tmp_path):
    p = _write_csv(tmp_path / "data.csv", {"x": [-1.0, -2.0]})
    with pytest.raises(ValueError, match="No valid"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            load(p, column="x", unit="µm")
