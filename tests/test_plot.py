"""Tests for stamp.plot."""

import warnings

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")  # non-interactive backend for tests
import matplotlib.pyplot as plt

from stamp._types import MeasurementData
from stamp.plot import (
    comparison_plot,
    distribution,
    distribution_profile,
    qq_plot,
    saltykov_plot,
    twostep_plot,
)
from stamp.simulate import simulate_section
from stamp.stats import fit
from stamp.stereo import saltykov, two_step


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def _mdata(n=200, seed=0):
    rng = np.random.default_rng(seed)
    return MeasurementData(
        values=rng.lognormal(mean=2.0, sigma=0.4, size=n),
        unit="µm",
        label="Grain ECD",
    )


# ---------------------------------------------------------------------------
# distribution
# ---------------------------------------------------------------------------


def test_distribution_returns_figure():
    fig = distribution(_mdata())
    assert isinstance(fig, plt.Figure)


def test_distribution_density_unit_uses_mathtext_inverse():
    fig = distribution(_mdata())
    ylabel = fig.axes[0].get_ylabel()
    assert "$^{-1}$" in ylabel
    assert "\u207b" not in ylabel

    fig_log = distribution(_mdata(), log_panel=True)
    for ax in fig_log.axes:
        ylabel = ax.get_ylabel()
        assert "$^{-1}$" in ylabel
        assert "\u207b" not in ylabel


def test_distribution_hist_only():
    fig = distribution(_mdata(), plot=("hist",))
    assert isinstance(fig, plt.Figure)


def test_distribution_kde_only():
    fig = distribution(_mdata(), plot=("kde",))
    assert isinstance(fig, plt.Figure)


def test_distribution_with_fit_overlay():
    data = _mdata()
    fit_result = fit(data, distribution="lognormal")
    fig = distribution(data, fit=fit_result)
    assert isinstance(fig, plt.Figure)


def test_distribution_saves_file(tmp_path):
    p = tmp_path / "dist.png"
    distribution(_mdata(), output_path=p)
    assert p.exists()


def test_distribution_invalid_plot_element():
    with pytest.raises(ValueError, match="plot"):
        distribution(_mdata(), plot=("invalid",))


def test_distribution_invalid_avg_element():
    with pytest.raises(ValueError, match="avg"):
        distribution(_mdata(), avg=("unknown",))


def test_distribution_log_panel_two_axes():
    fig = distribution(_mdata(), log_panel=True)
    assert isinstance(fig, plt.Figure)
    assert len(fig.axes) == 2


def test_distribution_bw_mode():
    from stamp.export import JournalStyle, journal_style

    data = _mdata()
    with journal_style(JournalStyle(preset="nature")):
        fig = distribution(data, avg=("amean",))
    assert isinstance(fig, plt.Figure)


# ---------------------------------------------------------------------------
# saltykov_plot
# ---------------------------------------------------------------------------


def test_saltykov_plot_returns_figure():
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sal = saltykov(_mdata())
    fig = saltykov_plot(sal)
    assert isinstance(fig, plt.Figure)


def test_saltykov_plot_two_axes():
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sal = saltykov(_mdata())
    fig = saltykov_plot(sal)
    assert len(fig.axes) == 2


def test_saltykov_plot_saves_file(tmp_path):
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sal = saltykov(_mdata())
    p = tmp_path / "sal.png"
    saltykov_plot(sal, output_path=p)
    assert p.exists()


# ---------------------------------------------------------------------------
# twostep_plot
# ---------------------------------------------------------------------------


def test_twostep_plot_returns_figure():
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ts = two_step(_mdata(), bin_range=(5, 10))
    fig = twostep_plot(ts)
    assert isinstance(fig, plt.Figure)


def test_twostep_plot_saves_file(tmp_path):
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ts = two_step(_mdata(), bin_range=(5, 10))
    p = tmp_path / "ts.png"
    twostep_plot(ts, output_path=p)
    assert p.exists()


# ---------------------------------------------------------------------------
# distribution_profile
# ---------------------------------------------------------------------------


def test_distribution_profile_pdf():
    fig = distribution_profile(_mdata(), kind="pdf")
    assert isinstance(fig, plt.Figure)


def test_distribution_profile_cdf():
    fig = distribution_profile(_mdata(), kind="cdf")
    assert isinstance(fig, plt.Figure)


def test_distribution_profile_with_fit():
    data = _mdata()
    fit_result = fit(data, distribution="lognormal")
    fig = distribution_profile(data, kind="pdf", fit=fit_result)
    assert isinstance(fig, plt.Figure)


def test_distribution_profile_saves_file(tmp_path):
    p = tmp_path / "profile.png"
    distribution_profile(_mdata(), output_path=p)
    assert p.exists()


def test_distribution_profile_invalid_kind():
    with pytest.raises(ValueError, match="kind"):
        distribution_profile(_mdata(), kind="bar")


# ---------------------------------------------------------------------------
# qq_plot
# ---------------------------------------------------------------------------


def test_qq_plot_returns_figure():
    fig = qq_plot(_mdata())
    assert isinstance(fig, plt.Figure)


def test_qq_plot_normal():
    rng = np.random.default_rng(0)
    data = MeasurementData(values=rng.normal(10, 2, 200), unit="µm", label="Test")
    fig = qq_plot(data, distribution="normal")
    assert isinstance(fig, plt.Figure)


def test_qq_plot_saves_file(tmp_path):
    p = tmp_path / "qq.png"
    qq_plot(_mdata(), output_path=p)
    assert p.exists()


def test_qq_plot_invalid_distribution():
    with pytest.raises(ValueError, match="distribution"):
        qq_plot(_mdata(), distribution="gamma")


# ---------------------------------------------------------------------------
# comparison_plot
# ---------------------------------------------------------------------------


@pytest.fixture
def sim_and_sal():
    sim = simulate_section(
        mu=45.0, sigma=0.35, n_intersections=100, n_grains=500, seed=0
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sal = saltykov(sim.apparent_diameters, n_bins=8)
    return sim, sal


def test_comparison_plot_returns_figure(sim_and_sal):
    sim, sal = sim_and_sal
    fig = comparison_plot(sim, sal)
    assert isinstance(fig, plt.Figure)


def test_comparison_plot_two_panels(sim_and_sal):
    sim, sal = sim_and_sal
    fig = comparison_plot(sim, sal)
    assert len(fig.axes) == 2


def test_comparison_plot_with_saltykov(sim_and_sal):
    sim, sal = sim_and_sal
    fig = comparison_plot(sim, sal)
    assert isinstance(fig, plt.Figure)


def test_comparison_plot_with_twostep():
    import warnings

    sim = simulate_section(
        mu=45.0, sigma=0.35, n_intersections=100, n_grains=500, seed=0
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ts = two_step(sim.apparent_diameters, bin_range=(5, 10))
    fig = comparison_plot(sim, ts)
    assert isinstance(fig, plt.Figure)


def test_comparison_plot_saves_file(sim_and_sal, tmp_path):
    sim, sal = sim_and_sal
    p = tmp_path / "comparison.png"
    comparison_plot(sim, sal, output_path=p)
    assert p.exists()


def test_comparison_plot_invalid_corrected_type(sim_and_sal):
    sim, _ = sim_and_sal
    with pytest.raises(TypeError, match="corrected"):
        comparison_plot(sim, "not_a_result")
