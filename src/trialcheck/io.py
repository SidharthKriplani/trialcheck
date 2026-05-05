"""Input loaders for TrialCheck examples and simple CSV/JSON exports."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Union

from .models import ExperimentSummary, GuardrailMetric, PrePeriodCovariate, VariantSummary
from .stats import safe_float, safe_int

PathLike = Union[str, Path]


def experiment_from_dict(data: Dict[str, Any]) -> ExperimentSummary:
    control = data.get("control", {})
    treatment = data.get("treatment", {})
    return ExperimentSummary(
        experiment_id=str(data.get("experiment_id", "experiment_unknown")),
        metric_name=str(data.get("metric_name", "primary_metric")),
        control=VariantSummary(
            name=str(control.get("name", "control")),
            n=int(control.get("n", 0)),
            conversions=_maybe_int(control.get("conversions")),
            mean=_maybe_float(control.get("mean")),
            std=_maybe_float(control.get("std")),
        ),
        treatment=VariantSummary(
            name=str(treatment.get("name", "treatment")),
            n=int(treatment.get("n", 0)),
            conversions=_maybe_int(treatment.get("conversions")),
            mean=_maybe_float(treatment.get("mean")),
            std=_maybe_float(treatment.get("std")),
        ),
        expected_control_ratio=float(data.get("expected_control_ratio", 0.5)),
        alpha=float(data.get("alpha", 0.05)),
        planned_duration_days=_maybe_int(data.get("planned_duration_days")),
        actual_duration_days=_maybe_int(data.get("actual_duration_days")),
        interim_looks=int(data.get("interim_looks", 0)),
        mde=_maybe_float(data.get("mde")),
        practical_threshold=_maybe_float(data.get("practical_threshold")),
        guardrails=[_guardrail_from_dict(row) for row in data.get("guardrails", [])],
        pre_period_covariates=[_covariate_from_dict(row) for row in data.get("pre_period_covariates", [])],
        metadata=dict(data.get("metadata", {})),
    )


def load_experiment_json(path: PathLike) -> ExperimentSummary:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return experiment_from_dict(data)


def load_experiment_csv(path: PathLike) -> ExperimentSummary:
    """Load a one-row summary CSV.

    Expected columns include:
    experiment_id, metric_name, control_n, control_conversions,
    treatment_n, treatment_conversions, expected_control_ratio,
    planned_duration_days, actual_duration_days, interim_looks, mde,
    practical_threshold.
    """

    with Path(path).open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("CSV file contains no rows")
    row = rows[0]
    return ExperimentSummary(
        experiment_id=row.get("experiment_id") or "experiment_unknown",
        metric_name=row.get("metric_name") or "primary_metric",
        control=VariantSummary(
            name=row.get("control_name") or "control",
            n=safe_int(row.get("control_n")) or 0,
            conversions=safe_int(row.get("control_conversions")),
        ),
        treatment=VariantSummary(
            name=row.get("treatment_name") or "treatment",
            n=safe_int(row.get("treatment_n")) or 0,
            conversions=safe_int(row.get("treatment_conversions")),
        ),
        expected_control_ratio=safe_float(row.get("expected_control_ratio")) or 0.5,
        alpha=safe_float(row.get("alpha")) or 0.05,
        planned_duration_days=safe_int(row.get("planned_duration_days")),
        actual_duration_days=safe_int(row.get("actual_duration_days")),
        interim_looks=safe_int(row.get("interim_looks")) or 0,
        mde=safe_float(row.get("mde")),
        practical_threshold=safe_float(row.get("practical_threshold")),
    )


def _maybe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _guardrail_from_dict(data: Dict[str, Any]) -> GuardrailMetric:
    return GuardrailMetric(
        name=str(data["name"]),
        control_value=float(data["control_value"]),
        treatment_value=float(data["treatment_value"]),
        bad_direction=str(data["bad_direction"]),
        tolerance=float(data.get("tolerance", 0.0)),
        unit=str(data.get("unit", "absolute")),
    )


def _covariate_from_dict(data: Dict[str, Any]) -> PrePeriodCovariate:
    return PrePeriodCovariate(
        name=str(data["name"]),
        control_mean=float(data["control_mean"]),
        treatment_mean=float(data["treatment_mean"]),
        control_std=float(data["control_std"]),
        treatment_std=float(data["treatment_std"]),
        control_n=int(data["control_n"]),
        treatment_n=int(data["treatment_n"]),
        max_abs_smd=float(data.get("max_abs_smd", 0.10)),
    )
