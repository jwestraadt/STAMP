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
]
