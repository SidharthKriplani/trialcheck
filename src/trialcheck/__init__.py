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
from .checks import minimum_sample_size_check, novelty_effect_check
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
    "minimum_sample_size_check",
    "novelty_effect_check",
    "to_json",
    "to_markdown",
    "to_html",
    "write_report",
]
