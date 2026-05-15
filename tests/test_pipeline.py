"""Tests for stamp.pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

import stamp.pipeline as pipeline
from stamp.pipeline import (
    FieldResult,
    PipelineResult,
    StateResult,
    boxplot,
    export_csv,
    run,
    run_batch,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

RNG = np.random.default_rng(0)


def _write_csv(path: Path, values: np.ndarray, col: str = "ecd") -> Path:
    pd.DataFrame({col: values}).to_csv(path, index=False)
    return path


@pytest.fixture()
def two_state_dir(tmp_path: Path):
    """Two states, two FOVs each, written as CSV files."""
    states = {}
    for state in ("StateA", "StateB"):
        d = tmp_path / state
        d.mkdir()
        for i in range(2):
            vals = RNG.lognormal(mean=np.log(10 + i * 2), sigma=0.3, size=80)
            _write_csv(d / f"fov{i}.csv", vals)
        states[state] = d
    return states


@pytest.fixture()
def file_list_states(tmp_path: Path):
    """Two states given as explicit file lists."""
    states = {}
    for state in ("Heat1", "Heat2"):
        files = []
        for i in range(3):
            vals = RNG.lognormal(mean=np.log(8 + i), sigma=0.25, size=60)
            p = _write_csv(tmp_path / f"{state}_fov{i}.csv", vals)
            files.append(p)
        states[state] = files
    return states


# ---------------------------------------------------------------------------
# _resolve_files
# ---------------------------------------------------------------------------


def test_resolve_files_directory(tmp_path):
    for name in ("a.csv", "b.csv", "ignore.txt"):
        (tmp_path / name).write_text("x\n1\n")
    files = pipeline._resolve_files(tmp_path)
    assert len(files) == 3  # .txt is also supported
    assert all(isinstance(f, Path) for f in files)


def test_resolve_files_single_file(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("x\n1\n")
    files = pipeline._resolve_files(p)
    assert files == [p]


def test_resolve_files_sequence(tmp_path):
    paths = [tmp_path / f"f{i}.csv" for i in range(3)]
    for p in paths:
        p.write_text("x\n1\n")
    files = pipeline._resolve_files(paths)
    assert files == paths


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


def test_run_returns_pipeline_result(two_state_dir):
    result = run(two_state_dir, column="ecd", unit="µm")
    assert isinstance(result, PipelineResult)
    assert len(result.states) == 2
    assert all(isinstance(sr, StateResult) for sr in result.states)


def test_run_field_count(two_state_dir):
    result = run(two_state_dir, column="ecd", unit="µm")
    for sr in result.states:
        assert len(sr.fields) == 2
        assert all(isinstance(fr, FieldResult) for fr in sr.fields)


def test_run_summary_shape(two_state_dir):
    result = run(two_state_dir, column="ecd", unit="µm")
    assert len(result.summary) == 4  # 2 states × 2 FOVs
    expected_cols = {"state", "fov", "file", "n", "unit", "amean", "gmean", "median"}
    assert expected_cols.issubset(result.summary.columns)


def test_run_with_file_list(file_list_states):
    result = run(file_list_states, column="ecd", unit="µm")
    assert len(result.summary) == 6  # 2 states × 3 FOVs


def test_run_invalid_metric(two_state_dir):
    with pytest.raises(ValueError, match="metric must be one of"):
        run(two_state_dir, column="ecd", unit="µm", metric="variance")


def test_run_empty_state_raises(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="No supported files found"):
        run({"Empty": empty_dir}, column="ecd", unit="µm")


def test_run_output_dir(two_state_dir, tmp_path):
    out = tmp_path / "output"
    result = run(two_state_dir, column="ecd", unit="µm", output_dir=out)
    assert (out / "pipeline_summary.csv").exists()
    assert (out / "boxplot_amean.png").exists()
    assert isinstance(result, PipelineResult)


@pytest.mark.parametrize("metric", ["amean", "gmean", "median"])
def test_run_metrics(two_state_dir, metric):
    result = run(two_state_dir, column="ecd", unit="µm", metric=metric)
    assert metric in result.summary.columns


# ---------------------------------------------------------------------------
# boxplot()
# ---------------------------------------------------------------------------


def test_boxplot_returns_figure(two_state_dir):
    result = run(two_state_dir, column="ecd", unit="µm")
    fig = boxplot(result)
    assert isinstance(fig, Figure)
    import matplotlib.pyplot as plt

    plt.close(fig)


@pytest.mark.parametrize("metric", ["amean", "gmean", "median"])
def test_boxplot_all_metrics(two_state_dir, metric):
    import matplotlib.pyplot as plt

    result = run(two_state_dir, column="ecd", unit="µm")
    fig = boxplot(result, metric=metric)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_boxplot_invalid_metric(two_state_dir):
    result = run(two_state_dir, column="ecd", unit="µm")
    with pytest.raises(ValueError, match="metric must be one of"):
        boxplot(result, metric="mode")


def test_boxplot_saves_file(two_state_dir, tmp_path):
    import matplotlib.pyplot as plt

    result = run(two_state_dir, column="ecd", unit="µm")
    out = tmp_path / "box.png"
    fig = boxplot(result, output_path=out)
    assert out.exists()
    plt.close(fig)


# ---------------------------------------------------------------------------
# export_csv()
# ---------------------------------------------------------------------------


def test_export_csv_creates_file(two_state_dir, tmp_path):
    result = run(two_state_dir, column="ecd", unit="µm")
    out = tmp_path / "summary.csv"
    export_csv(result, out)
    assert out.exists()


def test_export_csv_roundtrip(two_state_dir, tmp_path):
    result = run(two_state_dir, column="ecd", unit="µm")
    out = tmp_path / "summary.csv"
    export_csv(result, out)
    df = pd.read_csv(out)
    pd.testing.assert_frame_equal(df, result.summary)


def test_export_csv_columns(two_state_dir, tmp_path):
    result = run(two_state_dir, column="ecd", unit="µm")
    out = tmp_path / "summary.csv"
    export_csv(result, out)
    df = pd.read_csv(out)
    for col in ("state", "fov", "n", "amean", "gmean", "median", "p25", "p75"):
        assert col in df.columns


# ---------------------------------------------------------------------------
# run_batch()
# ---------------------------------------------------------------------------


def _write_batch_csv(path: Path, state: str, n_fovs: int, n_grains: int) -> Path:
    """Write a batch CSV with label = {state}_fov{N:02d}_grain{M:03d}."""
    rows = []
    for fov in range(1, n_fovs + 1):
        vals = RNG.lognormal(mean=np.log(10), sigma=0.3, size=n_grains)
        for g_idx, v in enumerate(vals, start=1):
            rows.append({"label": f"{state}_fov{fov:02d}_grain{g_idx:03d}", "ecd": v})
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


@pytest.fixture()
def batch_states(tmp_path):
    """Two states as batch CSV files, 3 FOVs × 50 grains each."""
    return {
        "StateA": _write_batch_csv(tmp_path / "stateA.csv", "StateA", 3, 50),
        "StateB": _write_batch_csv(tmp_path / "stateB.csv", "StateB", 3, 50),
    }


def test_run_batch_returns_pipeline_result(batch_states):
    result = run_batch(batch_states, measurement_column="ecd", unit="µm")
    assert isinstance(result, PipelineResult)
    assert len(result.states) == 2


def test_run_batch_fov_count(batch_states):
    result = run_batch(batch_states, measurement_column="ecd", unit="µm")
    for sr in result.states:
        assert len(sr.fields) == 3


def test_run_batch_fov_id_set(batch_states):
    result = run_batch(batch_states, measurement_column="ecd", unit="µm")
    for sr in result.states:
        for fr in sr.fields:
            assert fr.fov_id is not None
            assert fr.fov_id.startswith("fov")


def test_run_batch_fov_id_in_summary(batch_states):
    result = run_batch(batch_states, measurement_column="ecd", unit="µm")
    fov_values = result.summary["fov"].tolist()
    assert all(v.startswith("fov") for v in fov_values)


def test_run_batch_summary_shape(batch_states):
    result = run_batch(batch_states, measurement_column="ecd", unit="µm")
    assert len(result.summary) == 6  # 2 states × 3 FOVs


def test_run_batch_natural_sort(tmp_path):
    """FOVs are returned in natural order: fov1 < fov2 < ... < fov10."""
    rows = []
    for fov in range(1, 11):
        for g in range(1, 11):
            rows.append(
                {"label": f"S_fov{fov}_grain{g:02d}", "ecd": RNG.lognormal(2, 0.3)}
            )
    path = tmp_path / "s.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    result = run_batch({"S": path}, measurement_column="ecd", unit="µm")
    fov_ids = result.summary["fov"].tolist()
    assert fov_ids == [f"fov{i}" for i in range(1, 11)]


def test_run_batch_invalid_metric(batch_states):
    with pytest.raises(ValueError, match="metric must be one of"):
        run_batch(batch_states, measurement_column="ecd", unit="µm", metric="variance")


def test_run_batch_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_batch({"S": tmp_path / "missing.csv"}, measurement_column="ecd", unit="µm")


def test_run_batch_no_fov_match(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame(
        {"label": ["state_A_grain001", "state_A_grain002"], "ecd": [1.0, 2.0]}
    ).to_csv(path, index=False)
    with pytest.raises(ValueError, match="No FOV groups found"):
        run_batch({"S": path}, measurement_column="ecd", unit="µm")


def test_run_batch_output_dir(batch_states, tmp_path):
    out = tmp_path / "output"
    result = run_batch(
        batch_states, measurement_column="ecd", unit="µm", output_dir=out
    )
    assert (out / "pipeline_summary.csv").exists()
    assert (out / "boxplot_amean.png").exists()
    assert isinstance(result, PipelineResult)


@pytest.mark.parametrize("metric", ["amean", "gmean", "median"])
def test_run_batch_metrics(batch_states, metric):
    result = run_batch(batch_states, measurement_column="ecd", unit="µm", metric=metric)
    assert metric in result.summary.columns


def test_run_batch_integer_columns(tmp_path):
    """Measurement and label columns specified as integer indices."""
    path = tmp_path / "int_cols.csv"
    pd.DataFrame({"label": ["S_fov01_g001", "S_fov01_g002"], "ecd": [3.0, 4.0]}).to_csv(
        path, index=False
    )
    result = run_batch({"S": path}, measurement_column=1, unit="µm", label_column=0)
    assert len(result.summary) == 1
    assert result.summary["fov"].iloc[0] == "fov01"
