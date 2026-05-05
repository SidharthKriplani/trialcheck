"""TrialCheck: platform-agnostic A/B experiment readout auditing."""

from .auditor import TrialCheck
from .models import (
    CheckResult,
    CheckStatus,
    ExperimentSummary,
    GuardrailMetric,
    PrePeriodCovariate,
    TrialReport,
    VariantSummary,
)
from .reporting import to_html, to_json, to_markdown, write_report

__all__ = [
    "TrialCheck",
    "CheckResult",
    "CheckStatus",
    "ExperimentSummary",
    "GuardrailMetric",
    "PrePeriodCovariate",
    "TrialReport",
    "VariantSummary",
    "to_json",
    "to_markdown",
    "to_html",
    "write_report",
]
