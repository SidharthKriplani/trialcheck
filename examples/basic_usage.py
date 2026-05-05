"""Basic TrialCheck usage examples.

Example 1: Inline Python API (no file I/O needed)
Example 2: Load from JSON summary file
"""

# ── Example 1: Inline Python API ──────────────────────────────────────────────
from trialcheck import (
    ExperimentSummary,
    GuardrailMetric,
    PrePeriodCovariate,
    TrialCheck,
    VariantSummary,
)

experiment = ExperimentSummary(
    experiment_id="checkout-ui-v2",
    metric_name="checkout_conversion_rate",
    control=VariantSummary("control", n=15000, conversions=1350),
    treatment=VariantSummary("treatment", n=15000, conversions=1530),
    expected_control_ratio=0.5,
    alpha=0.05,
    planned_duration_days=14,
    actual_duration_days=14,
    interim_looks=0,
    mde=0.009,
    practical_threshold=0.008,
    guardrails=[
        GuardrailMetric(
            name="revenue_per_user",
            control_value=4.82,
            treatment_value=4.91,
            bad_direction="decrease",
            tolerance=0.05,
            unit="USD",
        ),
    ],
    pre_period_covariates=[
        PrePeriodCovariate(
            name="past_orders",
            control_mean=3.10,
            treatment_mean=3.09,
            control_std=2.40,
            treatment_std=2.41,
            control_n=15000,
            treatment_n=15000,
        ),
    ],
)

report = TrialCheck(experiment).run()

print(f"Overall: {report.overall_status.value}")
print(f"Interpretation: {report.interpretation}\n")

for check in report.checks:
    print(f"  [{check.status.value:20s}] {check.check}")


# ── Example 2: Load from JSON file ────────────────────────────────────────────
from pathlib import Path
from trialcheck import write_report
from trialcheck.io import load_experiment_json

ROOT = Path(__file__).resolve().parents[1]
experiment2 = load_experiment_json(ROOT / "sample_data" / "checkout_experiment_summary.json")
report2 = TrialCheck(experiment2).run()

write_report(report2, ROOT / "outputs" / "trialcheck_report.json")
write_report(report2, ROOT / "outputs" / "trialcheck_report.md")
write_report(report2, ROOT / "outputs" / "trialcheck_report.html")
