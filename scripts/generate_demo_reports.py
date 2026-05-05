"""Generate demo audit reports for all four canonical TrialCheck scenarios.

Scenarios
---------
1. clean_pass     -- balanced randomization, sufficient duration, lift meets MDE,
                     healthy guardrails. Shows what a ship-ready readout looks like.

2. srm_fail       -- 70/30 observed split against a 50/50 design. SRM fires FAIL.

3. peeking_warn   -- experiment called at 40% of planned duration with two interim
                     looks. Primary metric is significant but decision is not safe.

4. guardrail_harm -- primary metric improves but revenue-per-user and refund-rate
                     guardrails breach tolerance. Overall = FAIL.

Each scenario writes:
    outputs/<scenario>_report.{json,md,html}

The canonical checkout_experiment_summary.json is also run and its reports
overwrite outputs/trialcheck_report.{json,md,html} for backward compatibility.
"""

from __future__ import annotations

from pathlib import Path

from trialcheck import (
    ExperimentSummary,
    GuardrailMetric,
    PrePeriodCovariate,
    TrialCheck,
    VariantSummary,
    write_report,
)
from trialcheck.io import load_experiment_json

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS = [
    (
        "clean_pass",
        ExperimentSummary(
            experiment_id="checkout-ui-v2-clean",
            metric_name="checkout_conversion_rate",
            control=VariantSummary("control", n=15000, conversions=1350, mean=4.82, std=2.30),
            treatment=VariantSummary("treatment", n=15000, conversions=1530, mean=4.91, std=2.28),
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
                GuardrailMetric(
                    name="support_contact_rate",
                    control_value=0.031,
                    treatment_value=0.030,
                    bad_direction="increase",
                    tolerance=0.005,
                    unit="rate",
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
                    max_abs_smd=0.10,
                ),
            ],
        ),
    ),
    (
        "srm_fail",
        ExperimentSummary(
            experiment_id="checkout-ui-v2-srm",
            metric_name="checkout_conversion_rate",
            control=VariantSummary("control", n=14100, conversions=1269),
            treatment=VariantSummary("treatment", n=10900, conversions=1145),
            expected_control_ratio=0.5,
            alpha=0.05,
            planned_duration_days=14,
            actual_duration_days=14,
            interim_looks=0,
            mde=0.009,
            practical_threshold=0.008,
        ),
    ),
    (
        "peeking_warn",
        ExperimentSummary(
            experiment_id="checkout-ui-v2-peeking",
            metric_name="checkout_conversion_rate",
            control=VariantSummary("control", n=5800, conversions=522),
            treatment=VariantSummary("treatment", n=5800, conversions=603),
            expected_control_ratio=0.5,
            alpha=0.05,
            planned_duration_days=14,
            actual_duration_days=5,
            interim_looks=2,
            mde=0.009,
            practical_threshold=0.008,
            guardrails=[
                GuardrailMetric(
                    name="revenue_per_user",
                    control_value=4.82,
                    treatment_value=4.78,
                    bad_direction="decrease",
                    tolerance=0.05,
                    unit="USD",
                ),
            ],
        ),
    ),
    (
        "guardrail_harm",
        ExperimentSummary(
            experiment_id="checkout-ui-v2-guardrail",
            metric_name="checkout_conversion_rate",
            control=VariantSummary("control", n=15000, conversions=1350, mean=4.82, std=2.30),
            treatment=VariantSummary("treatment", n=15000, conversions=1530, mean=4.91, std=2.28),
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
                    treatment_value=4.61,
                    bad_direction="decrease",
                    tolerance=0.05,
                    unit="USD",
                ),
                GuardrailMetric(
                    name="refund_rate",
                    control_value=0.020,
                    treatment_value=0.038,
                    bad_direction="increase",
                    tolerance=0.005,
                    unit="rate",
                ),
            ],
        ),
    ),
]

# ---------------------------------------------------------------------------
# Run all scenarios
# ---------------------------------------------------------------------------

for name, exp in SCENARIOS:
    report = TrialCheck(exp).run()
    for suffix in ("json", "md", "html"):
        write_report(report, OUTPUTS / f"{name}_report.{suffix}")
    print(f"{name:<22} overall={report.overall_status.value}")

# ---------------------------------------------------------------------------
# Also run the canonical checkout experiment (backward compat)
# ---------------------------------------------------------------------------

checkout_path = ROOT / "sample_data" / "checkout_experiment_summary.json"
if checkout_path.exists():
    checkout_exp = load_experiment_json(checkout_path)
    checkout_report = TrialCheck(checkout_exp).run()
    for suffix in ("json", "md", "html"):
        write_report(checkout_report, OUTPUTS / f"trialcheck_report.{suffix}")
    print(f"{'checkout (canonical)':<22} overall={checkout_report.overall_status.value}")

print("\nAll demo reports written to outputs/")
