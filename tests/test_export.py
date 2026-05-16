import matplotlib

matplotlib.use("Agg")

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from stamp.export import (
    DEFAULT,
    JAMA,
    NATURE,
    JournalStyle,
    apply_style,
    bw_bars,
    figure_for,
    journal_style,
    panel_label,
    save,
    to_csv,
    to_latex,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture()
def default_style():
    return JournalStyle()


@pytest.fixture()
def nature_style():
    return JournalStyle(preset="nature")


@pytest.fixture()
def simple_fig():
    fig, ax = plt.subplots()
    ax.plot([1, 2], [3, 4])
    return fig


@pytest.fixture()
def sample_df():
    return pd.DataFrame(
        {
            "Label": ["A", "B", "C"],
            "Value": [1.234567, 2.345678, 3.456789],
            "Count": [10, 20, 30],
        }
    )


# ── BR1: JournalStyle() resolves all fields ───────────────────────────────────


def test_br1_default_all_fields_resolved():
    style = JournalStyle()
    for field in (
        "font_family",
        "font_size",
        "tick_size",
        "legend_size",
        "line_width",
        "axis_line_width",
        "tick_length",
        "single_col_mm",
        "one_half_col_mm",
        "double_col_mm",
        "dpi",
    ):
        assert getattr(style, field) is not None, f"{field} was not resolved"


# ── BR2: nature preset resolves to specified values ───────────────────────────


def test_br2_nature_preset_values(nature_style):
    assert nature_style.single_col_mm == 89.0
    assert nature_style.font_size == 7.0


# ── BR3: unknown preset raises ValueError ─────────────────────────────────────


def test_br3_unknown_preset_raises():
    with pytest.raises(ValueError, match="unknown"):
        JournalStyle(preset="unknown")


# ── BR4: explicit field overrides preset; others keep preset value ─────────────


def test_br4_field_override(nature_style):
    custom = JournalStyle(preset="nature", font_size=9.0)
    assert custom.font_size == 9.0
    assert custom.tick_size == nature_style.tick_size


# ── BR5: journal_style sets rcParams correctly ────────────────────────────────


def test_br5_rcparams_set_inside_context(default_style):
    with journal_style(default_style):
        assert matplotlib.rcParams["axes.spines.top"] is False
        assert matplotlib.rcParams["axes.spines.right"] is False
        assert matplotlib.rcParams["xtick.direction"] == "out"
        assert matplotlib.rcParams["ytick.direction"] == "out"
        assert matplotlib.rcParams["axes.grid"] is False


# ── BR6: rcParams restored after context exits ────────────────────────────────


def test_br6_rcparams_restored_after_context(default_style):
    before_grid = matplotlib.rcParams["axes.grid"]
    before_top_spine = matplotlib.rcParams["axes.spines.top"]

    with journal_style(default_style):
        pass  # inside context: modified

    assert matplotlib.rcParams["axes.grid"] == before_grid
    assert matplotlib.rcParams["axes.spines.top"] == before_top_spine


# ── BR7: missing font emits UserWarning ───────────────────────────────────────


def test_br7_missing_font_warns():
    style = JournalStyle(font_family="NonExistentFontXYZ999")
    with pytest.warns(UserWarning, match="NonExistentFontXYZ999"):
        with journal_style(style):
            pass


# ── BR8: figure_for returns correct width ────────────────────────────────────


def test_br8_figure_for_single_width(default_style):
    fig = figure_for(default_style, width="single")
    expected = default_style.single_col_mm / 25.4
    assert math.isclose(fig.get_figwidth(), expected, abs_tol=0.01)


# ── BR9: invalid width raises ValueError ─────────────────────────────────────


def test_br9_invalid_width_raises(default_style):
    with pytest.raises(ValueError, match="width"):
        figure_for(default_style, width="quarter")  # type: ignore[arg-type]


# ── BR10: save writes files and returns paths ─────────────────────────────────


def test_br10_save_multiple_formats(simple_fig, tmp_path):
    paths = save(simple_fig, tmp_path / "fig1", formats=["pdf", "png"])
    assert len(paths) == 2
    assert all(isinstance(p, Path) for p in paths)
    assert (tmp_path / "fig1.pdf").exists()
    assert (tmp_path / "fig1.png").exists()


# ── BR11: save raises if output directory missing ─────────────────────────────


def test_br11_save_missing_directory_raises(simple_fig, tmp_path):
    import re

    missing = tmp_path / "nonexistent" / "fig1"
    with pytest.raises(ValueError, match=re.escape(str(tmp_path / "nonexistent"))):
        save(simple_fig, missing)


# ── BR12: save raises for unrecognised format ─────────────────────────────────


def test_br12_save_unrecognised_format_raises(simple_fig, tmp_path):
    with pytest.raises(ValueError, match="bmp"):
        save(simple_fig, tmp_path / "fig1", formats=["bmp"])


# ── BR13: to_latex emits booktabs rules, no \hline, no | ─────────────────────


def test_br13_to_latex_booktabs(sample_df):
    result = to_latex(sample_df)
    assert r"\toprule" in result
    assert r"\midrule" in result
    assert r"\bottomrule" in result
    assert r"\hline" not in result
    # column format string must not contain |
    # extract the content between \begin{tabular}{ and }
    import re

    m = re.search(r"\\begin\{tabular\}\{([^}]+)\}", result)
    assert m is not None
    assert "|" not in m.group(1)


# ── BR14: units appended to column headers (µ escaped to \textmu{}) ──────────


def test_br14_units_in_header(sample_df):
    result = to_latex(sample_df, units={"Value": "µm"})
    assert r"(\textmu{}m)" in result


# ── BR15: footnotes in tablenotes block below \bottomrule ─────────────────────


def test_br15_footnotes_in_output(sample_df):
    result = to_latex(sample_df, footnotes={"a": "p < 0.05"})
    assert "p < 0.05" in result
    assert r"\begin{tablenotes}" in result
    # footnotes must come AFTER \bottomrule, not before
    assert result.index(r"\bottomrule") < result.index(r"\begin{tablenotes}")


# ── BR16: to_latex writes file when path given ───────────────────────────────


def test_br16_to_latex_writes_file(sample_df, tmp_path):
    out = tmp_path / "table.tex"
    result = to_latex(sample_df, path=out)
    assert isinstance(result, str)
    assert out.exists()
    assert out.read_text(encoding="utf-8") == result


# ── BR17: to_csv rounds numeric columns ──────────────────────────────────────


def test_br17_to_csv_rounding(sample_df, tmp_path):
    out = tmp_path / "table.csv"
    to_csv(sample_df, out, decimals=2)
    loaded = pd.read_csv(out)
    # Values should be rounded to 2 decimal places
    for val in loaded["Value"]:
        rounded = round(val, 2)
        assert math.isclose(val, rounded, abs_tol=1e-9)


# ── Additional: save default format is pdf ────────────────────────────────────


def test_save_default_format(simple_fig, tmp_path):
    paths = save(simple_fig, tmp_path / "fig")
    assert len(paths) == 1
    assert paths[0].suffix == ".pdf"


# ── Additional: figure_for 1.5 and double column widths ─────────────────────


@pytest.mark.parametrize(
    "width, attr",
    [("1.5", "one_half_col_mm"), ("double", "double_col_mm")],
)
def test_figure_for_other_widths(default_style, width, attr):
    fig = figure_for(default_style, width=width)
    expected = getattr(default_style, attr) / 25.4
    assert math.isclose(fig.get_figwidth(), expected, abs_tol=0.01)


# ── Additional: to_latex with caption and label wraps in table env ────────────


def test_to_latex_with_caption_and_label(sample_df):
    result = to_latex(sample_df, caption="My table.", label="tab:my")
    assert r"\begin{table}" in result
    assert r"\centering" in result
    assert r"\caption{My table.}" in result
    assert r"\label{tab:my}" in result
    assert r"\end{table}" in result


# ── Additional: to_latex without caption has no table env ─────────────────────


def test_to_latex_no_table_env(sample_df):
    result = to_latex(sample_df)
    assert r"\begin{table}" not in result
    assert r"\begin{tabular}" in result


# ── Additional: header escaping — µ and % ────────────────────────────────────


def test_latex_header_escapes_mu():
    df = pd.DataFrame({"ECD (µm)": [1.0, 2.0]})
    result = to_latex(df)
    assert r"\textmu{}" in result
    assert "µ" not in result


def test_latex_header_escapes_percent():
    df = pd.DataFrame({"95 % CI": [1.0, 2.0]})
    result = to_latex(df)
    assert r"\%" in result
    # bare unescaped % must not remain (would start a LaTeX comment)
    import re

    assert not re.search(r"(?<!\\)%", result)


# ── Additional: footnotes use threeparttable when present ────────────────────


def test_latex_footnotes_use_threeparttable(sample_df):
    result = to_latex(sample_df, footnotes={"a": "note"})
    assert r"\begin{threeparttable}" in result
    assert r"\end{threeparttable}" in result
    # tablenotes items use \item[key] syntax
    assert r"\item[a]" in result


def test_latex_no_threeparttable_without_footnotes(sample_df):
    result = to_latex(sample_df)
    assert r"\begin{threeparttable}" not in result


# ── Additional: siunitx=True uses S columns ──────────────────────────────────


def test_latex_siunitx_s_columns(sample_df):
    result = to_latex(sample_df, siunitx=True)
    assert "S[table-format=" in result
    # Non-numeric columns remain "l"
    import re

    m = re.search(r"\\begin\{tabular\}\{([^}]+)\}", result)
    assert m is not None
    assert m.group(1).startswith("l")  # first col is text


def test_latex_siunitx_nan_wrapped():
    df = pd.DataFrame({"Label": ["A"], "Value": [float("nan")]})
    result = to_latex(df, siunitx=True)
    assert "{---}" in result


def test_latex_nan_plain():
    df = pd.DataFrame({"Label": ["A"], "Value": [float("nan")]})
    result = to_latex(df)
    assert "---" in result
    assert "—" not in result  # no literal Unicode em-dash


# ── Additional: row_notes places \tnote{} in label column ────────────────────


def test_latex_row_notes():
    df = pd.DataFrame({"Method": ["A", "B"], "Score": [1.0, 2.0]})
    result = to_latex(
        df,
        footnotes={"a": "note"},
        row_notes={"A": "a"},
    )
    assert r"A\tnote{a}" in result
    assert r"B\tnote" not in result


def test_latex_percent_no_double_escape():
    df = pd.DataFrame({"95 % CI": [1.0, 2.0]})
    result = to_latex(df)
    # must have thin-space \,\% but NOT \\% (double backslash)
    assert r"\,\%" in result
    assert r"\\%" not in result


# ── Preset constants ──────────────────────────────────────────────────────────


def test_preset_constants_are_journal_style_instances():
    assert isinstance(DEFAULT, JournalStyle)
    assert isinstance(NATURE, JournalStyle)
    assert isinstance(JAMA, JournalStyle)


def test_nature_constant_matches_preset():
    assert NATURE.font_size == 7.0
    assert NATURE.single_col_mm == 89.0
    assert NATURE.bw is True


def test_jama_constant_values():
    assert JAMA.single_col_mm == 85.0
    assert JAMA.double_col_mm == 175.0
    assert JAMA.bw is False


def test_panel_label_size_field_resolved():
    assert DEFAULT.panel_label_size == 8.0
    assert NATURE.panel_label_size == 8.0
    assert JAMA.panel_label_size == 8.0


# ── apply_style ───────────────────────────────────────────────────────────────


def test_apply_style_sets_pdf_fonttype(default_style):
    apply_style(default_style)
    assert matplotlib.rcParams["pdf.fonttype"] == 42
    assert matplotlib.rcParams["ps.fonttype"] == 42
    assert matplotlib.rcParams["axes.spines.top"] is False
    assert matplotlib.rcParams["axes.spines.right"] is False


# ── panel_label ───────────────────────────────────────────────────────────────


def test_panel_label_adds_text(simple_fig):
    ax = simple_fig.axes[0]
    before = len(ax.texts)
    panel_label(ax, "a", DEFAULT)
    assert len(ax.texts) == before + 1
    assert ax.texts[-1].get_text() == "a"
    assert ax.texts[-1].get_fontweight() == "bold"


def test_panel_label_default_size_without_spec(simple_fig):
    ax = simple_fig.axes[0]
    panel_label(ax, "b")
    assert ax.texts[-1].get_fontsize() == 8.0


# ── bw_bars ───────────────────────────────────────────────────────────────────


def test_bw_bars_draws_bars(simple_fig):
    ax = simple_fig.axes[0]
    bw_bars(ax, x=[1, 2, 3], height=[4, 5, 6], label="Series A")
    bars = [p for p in ax.patches]
    assert len(bars) == 3
    # First series: no hatch, white face
    assert bars[0].get_facecolor()[:3] == (1.0, 1.0, 1.0)


def test_bw_bars_hatch_cycle(simple_fig):
    ax = simple_fig.axes[0]
    bw_bars(ax, x=[1], height=[1], series_idx=0)
    bw_bars(ax, x=[1], height=[1], series_idx=1)
    patches = list(ax.patches)
    assert patches[0].get_hatch() == ""
    assert patches[1].get_hatch() != ""


# ── distribution with style= parameter ───────────────────────────────────────


def test_distribution_style_parameter():
    from stamp._types import MeasurementData
    from stamp.plot import distribution

    rng = np.random.default_rng(0)
    data = MeasurementData(
        values=rng.lognormal(mean=2.0, sigma=0.4, size=100),
        unit="µm",
        label="ECD",
    )
    fig = distribution(data, avg=(), style=DEFAULT)
    assert isinstance(fig, plt.Figure)


# ── figure_for uses constrained layout ───────────────────────────────────────


def test_figure_for_constrained_layout(default_style):
    fig = figure_for(default_style)
    assert fig.get_layout_engine() is not None
