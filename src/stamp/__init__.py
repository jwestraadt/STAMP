from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("stamp")
except PackageNotFoundError:
    __version__ = "unknown"

from stamp._types import (
    DescribeResult,
    FitResult,
    MeanResult,
    MeasurementData,
    MedianResult,
    PeakResult,
    SaltykovResult,
    SimulationResult,
    TwoStepResult,
)
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

__all__ = [
    "__version__",
    "MeasurementData",
    "SaltykovResult",
    "TwoStepResult",
    "SimulationResult",
    "MeanResult",
    "MedianResult",
    "PeakResult",
    "FitResult",
    "DescribeResult",
    "JournalStyle",
    "DEFAULT",
    "NATURE",
    "JAMA",
    "apply_style",
    "journal_style",
    "figure_for",
    "panel_label",
    "bw_bars",
    "save",
    "to_csv",
    "to_latex",
]
