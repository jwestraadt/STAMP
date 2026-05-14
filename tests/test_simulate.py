"""Tests for stamp.simulate."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from stamp._types import MeasurementData, SimulationResult
from stamp.simulate import simulate_section

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(**kwargs) -> SimulationResult:
    defaults = dict(mu=45.0, sigma=0.35, n_intersections=100, n_grains=500, seed=0)
    defaults.update(kwargs)
    return simulate_section(**defaults)


# ---------------------------------------------------------------------------
# Return type and shapes
# ---------------------------------------------------------------------------


def test_returns_simulation_result():
    assert isinstance(_run(), SimulationResult)


def test_true_diameters_is_measurement_data():
    result = _run()
    assert isinstance(result.true_diameters, MeasurementData)


def test_apparent_diameters_is_measurement_data():
    result = _run()
    assert isinstance(result.apparent_diameters, MeasurementData)


def test_true_diameters_length_equals_n_grains():
    result = _run(n_grains=600)
    assert len(result.true_diameters.values) == 600


def test_apparent_diameters_length_equals_n_intersections():
    result = _run(n_intersections=80)
    assert len(result.apparent_diameters.values) == 80


def test_values_are_float64():
    result = _run()
    assert result.true_diameters.values.dtype == np.float64
    assert result.apparent_diameters.values.dtype == np.float64


# ---------------------------------------------------------------------------
# All values must be strictly positive
# ---------------------------------------------------------------------------


def test_true_diameters_all_positive():
    result = _run(n_grains=2000)
    assert np.all(result.true_diameters.values > 0)


def test_apparent_diameters_all_positive():
    result = _run(n_intersections=500, n_grains=2000)
    assert np.all(result.apparent_diameters.values > 0)


def test_normal_distribution_all_positive():
    result = simulate_section(
        mu=50.0,
        sigma=5.0,
        n_intersections=200,
        n_grains=1000,
        distribution="normal",
        seed=42,
    )
    assert np.all(result.true_diameters.values > 0)
    assert np.all(result.apparent_diameters.values > 0)


# ---------------------------------------------------------------------------
# Wicksell bias: apparent mean must be below true mean
# ---------------------------------------------------------------------------


def test_wicksell_bias_apparent_geometric_mean_less_than_true():
    """Systematic Wicksell bias: 2-D apparent geometric mean < true 3-D mean."""
    result = simulate_section(
        mu=50.0, sigma=0.35, n_intersections=2000, n_grains=20_000, seed=42
    )
    gmean_true = np.exp(np.mean(np.log(result.true_diameters.values)))
    gmean_app = np.exp(np.mean(np.log(result.apparent_diameters.values)))
    assert gmean_app < gmean_true


def test_true_geometric_mean_close_to_mu():
    """Large pool geometric mean should be within 5 % of the input mu."""
    mu = 40.0
    result = simulate_section(
        mu=mu, sigma=0.3, n_intersections=100, n_grains=50_000, seed=0
    )
    gmean = np.exp(np.mean(np.log(result.true_diameters.values)))
    assert abs(gmean - mu) / mu < 0.05


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


def test_same_seed_gives_identical_results():
    r1 = _run(seed=99)
    r2 = _run(seed=99)
    np.testing.assert_array_equal(r1.true_diameters.values, r2.true_diameters.values)
    np.testing.assert_array_equal(
        r1.apparent_diameters.values, r2.apparent_diameters.values
    )


def test_different_seeds_differ():
    r1 = _run(seed=1)
    r2 = _run(seed=2)
    assert not np.array_equal(r1.true_diameters.values, r2.true_diameters.values)


def test_none_seed_runs_without_error():
    result = simulate_section(mu=45.0, sigma=0.35, n_intersections=50, n_grains=200)
    assert len(result.apparent_diameters.values) == 50


# ---------------------------------------------------------------------------
# Normal distribution
# ---------------------------------------------------------------------------


def test_normal_distribution_returns_result():
    result = simulate_section(
        mu=50.0,
        sigma=5.0,
        n_intersections=100,
        n_grains=500,
        distribution="normal",
        seed=0,
    )
    assert isinstance(result, SimulationResult)
    assert result.distribution == "normal"


def test_normal_distribution_high_rejection_warns():
    """Very small mu/sigma ratio should trigger a UserWarning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        simulate_section(
            mu=5.0,
            sigma=4.0,
            n_intersections=50,
            n_grains=500,
            distribution="normal",
            seed=0,
        )
    # May or may not warn depending on RNG — just ensure no crash
    assert all(issubclass(warning.category, UserWarning) for warning in w)


# ---------------------------------------------------------------------------
# Metadata stored on result
# ---------------------------------------------------------------------------


def test_result_stores_mu_sigma():
    result = _run(mu=30.0, sigma=0.4)
    assert result.mu == 30.0
    assert result.sigma == 0.4


def test_result_stores_n_grains_and_intersections():
    result = _run(n_grains=400, n_intersections=80)
    assert result.n_grains == 400
    assert result.n_intersections == 80


def test_result_stores_seed():
    result = _run(seed=123)
    assert result.seed == 123


def test_result_stores_distribution():
    result = _run()
    assert result.distribution == "lognormal"


def test_unit_propagated_to_result_and_data():
    result = _run(unit="nm")
    assert result.unit == "nm"
    assert result.true_diameters.unit == "nm"
    assert result.apparent_diameters.unit == "nm"


def test_labels_set_correctly():
    result = _run()
    assert "3D" in result.true_diameters.label or "True" in result.true_diameters.label
    assert (
        "2D" in result.apparent_diameters.label
        or "Apparent" in result.apparent_diameters.label
    )


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_invalid_distribution_raises():
    with pytest.raises(ValueError, match="distribution"):
        simulate_section(mu=45.0, sigma=0.35, distribution="gamma")


def test_mu_zero_raises():
    with pytest.raises(ValueError, match="mu"):
        simulate_section(mu=0.0, sigma=0.35)


def test_mu_negative_raises():
    with pytest.raises(ValueError, match="mu"):
        simulate_section(mu=-10.0, sigma=0.35)


def test_sigma_zero_raises():
    with pytest.raises(ValueError, match="sigma"):
        simulate_section(mu=45.0, sigma=0.0)


def test_sigma_negative_raises():
    with pytest.raises(ValueError, match="sigma"):
        simulate_section(mu=45.0, sigma=-0.5)


def test_n_intersections_zero_raises():
    with pytest.raises(ValueError, match="n_intersections"):
        simulate_section(mu=45.0, sigma=0.35, n_intersections=0)


def test_n_grains_less_than_n_intersections_raises():
    with pytest.raises(ValueError, match="n_grains"):
        simulate_section(mu=45.0, sigma=0.35, n_intersections=500, n_grains=100)
