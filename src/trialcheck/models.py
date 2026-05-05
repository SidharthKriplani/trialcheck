"""Core data models for TrialCheck.

The models deliberately stay lightweight and dependency-free so the library can
run in interview/demo environments without a database or experimentation vendor.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CheckStatus(str, Enum):
    """Standard check status used across all audit outputs."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    INSUFFICIENT_INPUT = "INSUFFICIENT_INPUT"


@dataclass(frozen=True)
class VariantSummary:
    """Observed assignment and primary metric summary for one variant."""

    name: str
    n: int
    conversions: Optional[int] = None
    mean: Optional[float] = None
    std: Optional[float] = None

    def rate(self) -> Optional[float]:
        if self.conversions is None or self.n <= 0:
            return None
        return self.conversions / self.n


@dataclass(frozen=True)
class GuardrailMetric:
    """Guardrail metric summary.

    bad_direction controls what movement should be treated as harmful:
    - "increase": treatment-control above tolerance is bad
    - "decrease": control-treatment above tolerance is bad
    """

    name: str
    control_value: float
    treatment_value: float
    bad_direction: str
    tolerance: float = 0.0
    unit: str = "absolute"


@dataclass(frozen=True)
class PrePeriodCovariate:
    """Pre-period covariate balance summary."""

    name: str
    control_mean: float
    treatment_mean: float
    control_std: float
    treatment_std: float
    control_n: int
    treatment_n: int
    max_abs_smd: float = 0.10


@dataclass(frozen=True)
class ExperimentSummary:
    """Input object for a completed A/B experiment readout audit."""

    experiment_id: str
    metric_name: str
    control: VariantSummary
    treatment: VariantSummary
    expected_control_ratio: float = 0.5
    alpha: float = 0.05
    planned_duration_days: Optional[int] = None
    actual_duration_days: Optional[int] = None
    interim_looks: int = 0
    mde: Optional[float] = None
    practical_threshold: Optional[float] = None
    min_sample_size: int = 100
    novelty_effect_days: int = 7
    guardrails: List[GuardrailMetric] = field(default_factory=list)
    pre_period_covariates: List[PrePeriodCovariate] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckResult:
    """Single audit check result."""

    check: str
    status: CheckStatus
    detail: str
    recommendation: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True)
class TrialReport:
    """Aggregate audit report for an experiment readout."""

    experiment_id: str
    metric_name: str
    overall_status: CheckStatus
    checks: List[CheckResult]
    interpretation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "metric_name": self.metric_name,
            "overall_status": self.overall_status.value,
            "interpretation": self.interpretation,
            "metadata": self.metadata,
            "checks": [check.to_dict() for check in self.checks],
        }
