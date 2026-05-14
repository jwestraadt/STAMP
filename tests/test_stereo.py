"""Tests for stamp.stereo."""

import warnings

import numpy as np
import pytest

from stamp._types import MeasurementData
from stamp.stereo import ecd_from_area, linear_intercept_correction, saltykov, two_step


def _mdata(values, unit="µm²", label="Test"):
    return MeasurementData(values=np.array(values, dtype=float), unit=unit, label=label)


# ---------------------------------------------------------------------------
# ecd_from_area
# ---------------------------------------------------------------------------


def test_ecd_from_area_formula():
    areas = np.array([np.pi])  # area = π → ECD = 2
    result = ecd_from_area(_mdata(areas))
    np.testing.assert_allclose(result.values, [2.0])


def test_ecd_from_area_multiple():
    areas = np.array([np.pi, 4 * np.pi])  # ECDs: 2, 4
    result = ecd_from_area(_mdata(areas))
    np.testing.assert_allclose(result.values, [2.0, 4.0])


def test_ecd_from_area_unit_strips_superscript():
    result = ecd_from_area(_mdata([np.pi], unit="µm²"))
    assert result.unit == "µm"


def test_ecd_from_area_unit_unchanged_when_no_superscript():
    result = ecd_from_area(_mdata([np.pi], unit="um2"))
    assert result.unit == "um2"


def test_ecd_from_area_label():
    result = ecd_from_area(_mdata([np.pi], label="Grain Area"))
    assert result.label == "ECD"


def test_ecd_from_area_returns_new_object():
    data = _mdata([np.pi])
    result = ecd_from_area(data)
    assert result is not data


# ---------------------------------------------------------------------------
# linear_intercept_correction
# ---------------------------------------------------------------------------


def test_linear_intercept_correction_formula():
    # D = (4/π) × L
    intercepts = np.array([np.pi / 4])  # → D = 1.0
    result = linear_intercept_correction(_mdata(intercepts, unit="µm"))
    np.testing.assert_allclose(result.values, [1.0])


def test_linear_intercept_correction_multiple():
    intercepts = np.array([1.0, 2.0])
    result = linear_intercept_correction(_mdata(intercepts, unit="µm"))
    np.testing.assert_allclose(result.values, np.array([1.0, 2.0]) * 4 / np.pi)


def test_linear_intercept_correction_label():
    result = linear_intercept_correction(_mdata([1.0], unit="µm"))
    assert result.label == "Corrected Grain Diameter"


def test_linear_intercept_correction_unit_preserved():
    result = linear_intercept_correction(_mdata([1.0], unit="µm"))
    assert result.unit == "µm"


# ---------------------------------------------------------------------------
# saltykov
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_diameters():
    rng = np.random.default_rng(42)
    return _mdata(rng.lognormal(mean=2.0, sigma=0.4, size=300), unit="µm", label="ECD")


def test_saltykov_returns_result(synthetic_diameters):
    from stamp._types import SaltykovResult

    result = saltykov(synthetic_diameters)
    assert isinstance(result, SaltykovResult)


def test_saltykov_bin_count(synthetic_diameters):
    result = saltykov(synthetic_diameters, n_bins=10)
    assert len(result.bin_midpoints) == 10
    assert len(result.freq3d) == 10
    assert len(result.cdf_vol) == 10
    assert len(result.bin_edges) == 11


def test_saltykov_freq3d_non_negative(synthetic_diameters):
    result = saltykov(synthetic_diameters)
    assert np.all(result.freq3d >= 0)


def test_saltykov_freq3d_normalised(synthetic_diameters):
    result = saltykov(synthetic_diameters, n_bins=10)
    integral = np.sum(result.freq3d * result.bin_width)
    np.testing.assert_allclose(integral, 1.0, atol=0.05)


def test_saltykov_cdf_vol_range(synthetic_diameters):
    result = saltykov(synthetic_diameters)
    assert result.cdf_vol[0] >= 0
    np.testing.assert_allclose(result.cdf_vol[-1], 100.0, atol=1e-6)


def test_saltykov_unit_and_label(synthetic_diameters):
    result = saltykov(synthetic_diameters)
    assert result.unit == "µm"
    assert result.label == "ECD"


def test_saltykov_invalid_n_bins(synthetic_diameters):
    with pytest.raises(ValueError, match="n_bins"):
        saltykov(synthetic_diameters, n_bins=1)
    with pytest.raises(ValueError, match="n_bins"):
        saltykov(synthetic_diameters, n_bins=30)


def test_saltykov_left_edge_min(synthetic_diameters):
    result = saltykov(synthetic_diameters, left_edge="min")
    assert result.bin_edges[0] == pytest.approx(synthetic_diameters.values.min())


def test_saltykov_negative_clipped_with_warning(synthetic_diameters):
    # Very few bins can produce negative unfolded frequencies.
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        result = saltykov(synthetic_diameters, n_bins=3)
    assert np.all(result.freq3d >= 0)


# ---------------------------------------------------------------------------
# two_step
# ---------------------------------------------------------------------------


def test_two_step_returns_result(synthetic_diameters):
    from stamp._types import TwoStepResult

    result = two_step(synthetic_diameters, bin_range=(5, 10))
    assert isinstance(result, TwoStepResult)


def test_two_step_geometric_mean_positive(synthetic_diameters):
    result = two_step(synthetic_diameters, bin_range=(5, 10))
    assert result.geometric_mean > 0


def test_two_step_shape_positive(synthetic_diameters):
    result = two_step(synthetic_diameters, bin_range=(5, 10))
    assert result.shape > 0


def test_two_step_best_n_bins_in_range(synthetic_diameters):
    result = two_step(synthetic_diameters, bin_range=(5, 12))
    assert 5 <= result.best_n_bins <= 12


def test_two_step_fit_curve_length(synthetic_diameters):
    result = two_step(synthetic_diameters, bin_range=(5, 10))
    assert len(result.fit_curve) == len(result.xgrid)
    assert len(result.fit_error) == len(result.xgrid)


def test_two_step_invalid_bin_range(synthetic_diameters):
    with pytest.raises(ValueError):
        two_step(synthetic_diameters, bin_range=(15, 10))
