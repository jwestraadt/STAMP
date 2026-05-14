"""Tests for stamp.stats."""

import numpy as np
import pytest

from stamp._types import (
    DescribeResult,
    FitResult,
    MeanResult,
    MeasurementData,
    MedianResult,
    PeakResult,
)
from stamp.stats import amean, describe, fit, freq_peak, gmean, median


def _mdata(values, unit="µm", label="Test"):
    return MeasurementData(values=np.array(values, dtype=float), unit=unit, label=label)


@pytest.fixture
def normal_data():
    rng = np.random.default_rng(0)
    return _mdata(rng.normal(loc=10.0, scale=2.0, size=500))


@pytest.fixture
def lognormal_data():
    rng = np.random.default_rng(1)
    return _mdata(rng.lognormal(mean=2.0, sigma=0.4, size=500))


# ---------------------------------------------------------------------------
# amean
# ---------------------------------------------------------------------------


def test_amean_returns_mean_result(normal_data):
    result = amean(normal_data)
    assert isinstance(result, MeanResult)


def test_amean_value_close_to_true(normal_data):
    result = amean(normal_data)
    assert abs(result.mean - 10.0) < 0.5


def test_amean_ci_bounds_ordered(normal_data):
    result = amean(normal_data)
    assert result.ci_low < result.mean < result.ci_high


def test_amean_ci_length_positive(normal_data):
    result = amean(normal_data)
    assert result.ci_length == pytest.approx(result.ci_high - result.ci_low)
    assert result.ci_length > 0


def test_amean_n_correct(normal_data):
    result = amean(normal_data)
    assert result.n == len(normal_data.values)


def test_amean_unit_and_label(normal_data):
    result = amean(normal_data)
    assert result.unit == normal_data.unit
    assert result.label == normal_data.label


def test_amean_methods(normal_data, lognormal_data):
    # ASTM uses t-distribution and brackets the sample mean
    r = amean(normal_data, method="ASTM")
    assert r.ci_low < r.mean < r.ci_high
    # GCI and mCox estimate the lognormal population arithmetic mean (exp(µ + σ²/2));
    # bounds are positive and ordered but need not bracket the sample arithmetic mean
    for method in ("GCI", "mCox"):
        result = amean(lognormal_data, method=method)
        assert 0 < result.ci_low < result.ci_high


def test_amean_invalid_method(normal_data):
    with pytest.raises(ValueError, match="method"):
        amean(normal_data, method="unknown")


def test_amean_invalid_ci(normal_data):
    with pytest.raises(ValueError, match="ci"):
        amean(normal_data, ci=1.5)


# ---------------------------------------------------------------------------
# gmean
# ---------------------------------------------------------------------------


def test_gmean_returns_mean_result(lognormal_data):
    result = gmean(lognormal_data)
    assert isinstance(result, MeanResult)


def test_gmean_value_positive(lognormal_data):
    result = gmean(lognormal_data)
    assert result.mean > 0


def test_gmean_ci_bounds_ordered(lognormal_data):
    result = gmean(lognormal_data)
    assert result.ci_low < result.mean < result.ci_high


def test_gmean_std_is_multiplicative(lognormal_data):
    result = gmean(lognormal_data)
    assert result.std > 1.0


def test_gmean_methods(lognormal_data):
    for method in ("CLT", "bayes"):
        result = gmean(lognormal_data, method=method)
        assert result.mean > 0


def test_gmean_invalid_method(lognormal_data):
    with pytest.raises(ValueError, match="method"):
        gmean(lognormal_data, method="ASTM")


# ---------------------------------------------------------------------------
# median
# ---------------------------------------------------------------------------


def test_median_returns_median_result(normal_data):
    result = median(normal_data)
    assert isinstance(result, MedianResult)


def test_median_value_close_to_true(normal_data):
    result = median(normal_data)
    assert abs(result.median - 10.0) < 0.5


def test_median_iqr_positive(normal_data):
    result = median(normal_data)
    assert result.iqr > 0


def test_median_ci_bounds_ordered(normal_data):
    result = median(normal_data)
    assert result.ci_low < result.median < result.ci_high


def test_median_n(normal_data):
    result = median(normal_data)
    assert result.n == len(normal_data.values)


# ---------------------------------------------------------------------------
# freq_peak
# ---------------------------------------------------------------------------


def test_freq_peak_returns_peak_result(normal_data):
    result = freq_peak(normal_data)
    assert isinstance(result, PeakResult)


def test_freq_peak_near_true_mode(normal_data):
    result = freq_peak(normal_data)
    assert abs(result.peak - 10.0) < 1.0


def test_freq_peak_density_positive(normal_data):
    result = freq_peak(normal_data)
    assert result.peak_density > 0


def test_freq_peak_xgrid_density_same_length(normal_data):
    result = freq_peak(normal_data)
    assert len(result.xgrid) == len(result.density)


def test_freq_peak_bandwidth_silverman(normal_data):
    result = freq_peak(normal_data, bandwidth="silverman")
    assert result.bandwidth > 0


def test_freq_peak_bandwidth_scott(normal_data):
    result = freq_peak(normal_data, bandwidth="scott")
    assert result.bandwidth > 0


def test_freq_peak_bandwidth_scalar(normal_data):
    # 1.5 is the bandwidth scaling factor; resolved_bw = factor × std
    result = freq_peak(normal_data, bandwidth=1.5)
    assert result.bandwidth > 0


def test_freq_peak_invalid_bandwidth(normal_data):
    with pytest.raises(ValueError, match="bandwidth"):
        freq_peak(normal_data, bandwidth="auto")


def test_freq_peak_negative_bandwidth(normal_data):
    with pytest.raises(ValueError, match="bandwidth"):
        freq_peak(normal_data, bandwidth=-1.0)


# ---------------------------------------------------------------------------
# fit
# ---------------------------------------------------------------------------


def test_fit_normal_returns_fit_result(normal_data):
    result = fit(normal_data, distribution="normal")
    assert isinstance(result, FitResult)
    assert result.distribution == "normal"


def test_fit_lognormal_returns_fit_result(lognormal_data):
    result = fit(lognormal_data, distribution="lognormal")
    assert isinstance(result, FitResult)
    assert result.distribution == "lognormal"


def test_fit_normal_params_keys(normal_data):
    result = fit(normal_data, distribution="normal")
    assert "loc" in result.params
    assert "scale" in result.params


def test_fit_lognormal_params_keys(lognormal_data):
    result = fit(lognormal_data, distribution="lognormal")
    assert "s" in result.params
    assert "loc" in result.params
    assert "scale" in result.params


def test_fit_r_squared_range(normal_data):
    result = fit(normal_data, distribution="normal")
    assert 0.0 <= result.r_squared <= 1.0


def test_fit_ks_pvalue_range(normal_data):
    result = fit(normal_data, distribution="normal")
    assert 0.0 <= result.ks_pvalue <= 1.0


def test_fit_invalid_distribution(normal_data):
    with pytest.raises(ValueError, match="distribution"):
        fit(normal_data, distribution="gamma")


def test_fit_unit_label(normal_data):
    result = fit(normal_data, distribution="normal")
    assert result.unit == normal_data.unit
    assert result.label == normal_data.label


# ---------------------------------------------------------------------------
# describe
# ---------------------------------------------------------------------------


def test_describe_returns_describe_result(normal_data):
    result = describe(normal_data)
    assert isinstance(result, DescribeResult)


def test_describe_n(normal_data):
    result = describe(normal_data)
    assert result.n == len(normal_data.values)


def test_describe_percentile_keys(normal_data):
    result = describe(normal_data)
    assert set(result.percentiles.keys()) == {5, 10, 25, 75, 90, 95}


def test_describe_percentiles_ordered(normal_data):
    result = describe(normal_data)
    p = result.percentiles
    assert p[5] < p[10] < p[25] < p[75] < p[90] < p[95]


def test_describe_sub_results(normal_data):
    result = describe(normal_data)
    assert isinstance(result.amean, MeanResult)
    assert isinstance(result.gmean, MeanResult)
    assert isinstance(result.median, MedianResult)
    assert isinstance(result.peak, PeakResult)
