import json
import unittest
from pathlib import Path

from trialcheck import (
    CheckStatus,
    ExperimentSummary,
    GuardrailMetric,
    PrePeriodCovariate,
    TrialCheck,
    VariantSummary,
    to_json,
    to_markdown,
)


class TrialCheckTests(unittest.TestCase):
    def test_srm_fail_is_detected(self):
        exp = ExperimentSummary(
            experiment_id="srm_fail",
            metric_name="conversion",
            control=VariantSummary("control", n=700, conversions=70),
            treatment=VariantSummary("treatment", n=300, conversions=45),
            expected_control_ratio=0.5,
        )
        report = TrialCheck(exp).run()
        srm = next(c for c in report.checks if c.check == "Sample Ratio Mismatch")
        self.assertEqual(srm.status, CheckStatus.FAIL)
        self.assertEqual(report.overall_status, CheckStatus.FAIL)

    def test_practical_significance_warn_when_lift_below_threshold(self):
        exp = ExperimentSummary(
            experiment_id="small_lift",
            metric_name="conversion",
            control=VariantSummary("control", n=10000, conversions=1000),
            treatment=VariantSummary("treatment", n=10000, conversions=1050),
            practical_threshold=0.02,
            mde=0.02,
        )
        report = TrialCheck(exp).run()
        practical = next(c for c in report.checks if c.check == "Practical Significance")
        self.assertEqual(practical.status, CheckStatus.WARN)

    def test_guardrail_fail_when_harmful_movement_exceeds_tolerance(self):
        exp = ExperimentSummary(
            experiment_id="guardrail_fail",
            metric_name="conversion",
            control=VariantSummary("control", n=1000, conversions=100),
            treatment=VariantSummary("treatment", n=1000, conversions=120),
            guardrails=[
                GuardrailMetric(
                    name="refund_rate",
                    control_value=0.02,
                    treatment_value=0.04,
                    bad_direction="increase",
                    tolerance=0.005,
                )
            ],
        )
        report = TrialCheck(exp).run()
        guardrail = next(c for c in report.checks if c.check == "Guardrail: refund_rate")
        self.assertEqual(guardrail.status, CheckStatus.FAIL)

    def test_peeking_warn_when_called_early(self):
        exp = ExperimentSummary(
            experiment_id="early_call",
            metric_name="conversion",
            control=VariantSummary("control", n=1000, conversions=100),
            treatment=VariantSummary("treatment", n=1000, conversions=120),
            planned_duration_days=21,
            actual_duration_days=8,
        )
        report = TrialCheck(exp).run()
        peeking = next(c for c in report.checks if c.check == "Peeking / Early Readout Risk")
        self.assertEqual(peeking.status, CheckStatus.WARN)

    def test_pre_period_balance_warn_for_large_smd(self):
        exp = ExperimentSummary(
            experiment_id="imbalanced",
            metric_name="conversion",
            control=VariantSummary("control", n=1000, conversions=100),
            treatment=VariantSummary("treatment", n=1000, conversions=120),
            pre_period_covariates=[
                PrePeriodCovariate(
                    name="past_orders",
                    control_mean=1.0,
                    treatment_mean=1.5,
                    control_std=1.0,
                    treatment_std=1.0,
                    control_n=1000,
                    treatment_n=1000,
                    max_abs_smd=0.1,
                )
            ],
        )
        report = TrialCheck(exp).run()
        balance = next(c for c in report.checks if c.check == "Pre-period Balance: past_orders")
        self.assertEqual(balance.status, CheckStatus.WARN)

    def test_reports_render_json_and_markdown(self):
        exp = ExperimentSummary(
            experiment_id="render_test",
            metric_name="conversion",
            control=VariantSummary("control", n=1000, conversions=100),
            treatment=VariantSummary("treatment", n=1000, conversions=120),
        )
        report = TrialCheck(exp).run()
        payload = json.loads(to_json(report))
        self.assertEqual(payload["experiment_id"], "render_test")
        markdown = to_markdown(report)
        self.assertIn("TrialCheck Audit Report", markdown)
        self.assertIn("Sample Ratio Mismatch", markdown)


class ContinuousMetricTests(unittest.TestCase):
    """Tests for the Welch t-test continuous metric check."""

    def test_continuous_metric_pass_when_significant(self):
        # Large effect, large n — should be easily significant
        exp = ExperimentSummary(
            experiment_id="cont_pass",
            metric_name="revenue_per_user",
            control=VariantSummary("control", n=10000, mean=4.80, std=2.30),
            treatment=VariantSummary("treatment", n=10000, mean=5.20, std=2.30),
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Continuous Metric (Welch t-test)")
        self.assertEqual(check.status, CheckStatus.PASS)
        self.assertIn("t_stat", check.evidence)
        self.assertIn("dof", check.evidence)
        self.assertIn("p_value", check.evidence)

    def test_continuous_metric_warn_when_not_significant(self):
        # Tiny effect, moderate n — should not be significant
        exp = ExperimentSummary(
            experiment_id="cont_warn",
            metric_name="revenue_per_user",
            control=VariantSummary("control", n=100, mean=4.80, std=2.30),
            treatment=VariantSummary("treatment", n=100, mean=4.82, std=2.30),
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Continuous Metric (Welch t-test)")
        self.assertEqual(check.status, CheckStatus.WARN)

    def test_continuous_metric_skipped_without_mean_std(self):
        # Binary conversion experiment — no mean/std supplied
        exp = ExperimentSummary(
            experiment_id="cont_skip",
            metric_name="conversion",
            control=VariantSummary("control", n=1000, conversions=100),
            treatment=VariantSummary("treatment", n=1000, conversions=110),
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Continuous Metric (Welch t-test)")
        self.assertEqual(check.status, CheckStatus.INSUFFICIENT_INPUT)

    def test_continuous_metric_handles_zero_std(self):
        # Both variants have std=0 (degenerate) — should return INSUFFICIENT_INPUT
        exp = ExperimentSummary(
            experiment_id="cont_zero_std",
            metric_name="flag",
            control=VariantSummary("control", n=500, mean=1.0, std=0.0),
            treatment=VariantSummary("treatment", n=500, mean=1.0, std=0.0),
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Continuous Metric (Welch t-test)")
        self.assertEqual(check.status, CheckStatus.INSUFFICIENT_INPUT)

    def test_continuous_metric_absolute_lift_in_evidence(self):
        exp = ExperimentSummary(
            experiment_id="cont_lift",
            metric_name="session_duration",
            control=VariantSummary("control", n=5000, mean=120.0, std=40.0),
            treatment=VariantSummary("treatment", n=5000, mean=125.0, std=40.0),
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Continuous Metric (Welch t-test)")
        self.assertAlmostEqual(check.evidence["absolute_lift"], 5.0, places=4)


class EdgeCaseTests(unittest.TestCase):
    """Edge cases for existing checks."""

    def test_srm_pass_for_exact_50_50_split(self):
        exp = ExperimentSummary(
            experiment_id="exact_split",
            metric_name="conversion",
            control=VariantSummary("control", n=5000, conversions=500),
            treatment=VariantSummary("treatment", n=5000, conversions=510),
            expected_control_ratio=0.5,
        )
        report = TrialCheck(exp).run()
        srm = next(c for c in report.checks if c.check == "Sample Ratio Mismatch")
        self.assertEqual(srm.status, CheckStatus.PASS)

    def test_primary_metric_insufficient_input_when_no_conversions(self):
        exp = ExperimentSummary(
            experiment_id="no_conv",
            metric_name="revenue",
            control=VariantSummary("control", n=1000),
            treatment=VariantSummary("treatment", n=1000),
        )
        report = TrialCheck(exp).run()
        primary = next(c for c in report.checks if c.check == "Primary Metric Statistical Readout")
        self.assertEqual(primary.status, CheckStatus.INSUFFICIENT_INPUT)

    def test_guardrail_pass_within_tolerance(self):
        exp = ExperimentSummary(
            experiment_id="guardrail_ok",
            metric_name="conversion",
            control=VariantSummary("control", n=1000, conversions=100),
            treatment=VariantSummary("treatment", n=1000, conversions=110),
            guardrails=[
                GuardrailMetric(
                    name="latency_p99",
                    control_value=200.0,
                    treatment_value=203.0,
                    bad_direction="increase",
                    tolerance=10.0,
                    unit="ms",
                )
            ],
        )
        report = TrialCheck(exp).run()
        guardrail = next(c for c in report.checks if c.check == "Guardrail: latency_p99")
        self.assertEqual(guardrail.status, CheckStatus.PASS)

    def test_peeking_pass_at_full_duration(self):
        exp = ExperimentSummary(
            experiment_id="full_duration",
            metric_name="conversion",
            control=VariantSummary("control", n=5000, conversions=500),
            treatment=VariantSummary("treatment", n=5000, conversions=550),
            planned_duration_days=14,
            actual_duration_days=14,
            interim_looks=0,
        )
        report = TrialCheck(exp).run()
        peeking = next(c for c in report.checks if c.check == "Peeking / Early Readout Risk")
        self.assertEqual(peeking.status, CheckStatus.PASS)

    def test_mde_context_warn_when_lift_below_mde(self):
        exp = ExperimentSummary(
            experiment_id="mde_low",
            metric_name="conversion",
            control=VariantSummary("control", n=10000, conversions=1000),
            treatment=VariantSummary("treatment", n=10000, conversions=1030),
            mde=0.005,
        )
        report = TrialCheck(exp).run()
        mde_check = next(c for c in report.checks if c.check == "MDE Context")
        self.assertEqual(mde_check.status, CheckStatus.WARN)

    def test_overall_pass_when_all_checks_pass(self):
        exp = ExperimentSummary(
            experiment_id="all_pass",
            metric_name="checkout_conversion",
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
                GuardrailMetric("revenue_per_user", 4.82, 4.91, "decrease", 0.05, "USD"),
            ],
            pre_period_covariates=[
                PrePeriodCovariate("past_orders", 3.10, 3.09, 2.40, 2.41, 15000, 15000, 0.10),
            ],
        )
        report = TrialCheck(exp).run()
        self.assertEqual(report.overall_status, CheckStatus.PASS)


class MinimumSampleSizeTests(unittest.TestCase):
    """Tests for the minimum sample size check."""

    def test_warn_when_control_below_threshold(self):
        exp = ExperimentSummary(
            experiment_id="tiny_control",
            metric_name="conversion",
            control=VariantSummary("control", n=50, conversions=5),
            treatment=VariantSummary("treatment", n=1000, conversions=100),
            min_sample_size=100,
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Minimum Sample Size")
        self.assertEqual(check.status, CheckStatus.WARN)
        self.assertEqual(check.evidence["min_n_threshold"], 100)

    def test_warn_when_treatment_below_threshold(self):
        exp = ExperimentSummary(
            experiment_id="tiny_treatment",
            metric_name="conversion",
            control=VariantSummary("control", n=1000, conversions=100),
            treatment=VariantSummary("treatment", n=40, conversions=4),
            min_sample_size=100,
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Minimum Sample Size")
        self.assertEqual(check.status, CheckStatus.WARN)

    def test_pass_when_both_above_threshold(self):
        exp = ExperimentSummary(
            experiment_id="adequate_n",
            metric_name="conversion",
            control=VariantSummary("control", n=500, conversions=50),
            treatment=VariantSummary("treatment", n=500, conversions=55),
            min_sample_size=100,
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Minimum Sample Size")
        self.assertEqual(check.status, CheckStatus.PASS)

    def test_default_threshold_is_100(self):
        exp = ExperimentSummary(
            experiment_id="default_threshold",
            metric_name="conversion",
            control=VariantSummary("control", n=99, conversions=10),
            treatment=VariantSummary("treatment", n=99, conversions=11),
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Minimum Sample Size")
        self.assertEqual(check.status, CheckStatus.WARN)
        self.assertEqual(check.evidence["min_n_threshold"], 100)

    def test_evidence_contains_both_n_values(self):
        exp = ExperimentSummary(
            experiment_id="evidence_check",
            metric_name="conversion",
            control=VariantSummary("control", n=200, conversions=20),
            treatment=VariantSummary("treatment", n=180, conversions=19),
            min_sample_size=100,
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Minimum Sample Size")
        self.assertEqual(check.evidence["n_control"], 200)
        self.assertEqual(check.evidence["n_treatment"], 180)


class NoveltyEffectTests(unittest.TestCase):
    """Tests for the novelty effect risk check."""

    def test_warn_when_duration_below_threshold(self):
        exp = ExperimentSummary(
            experiment_id="short_run",
            metric_name="conversion",
            control=VariantSummary("control", n=1000, conversions=100),
            treatment=VariantSummary("treatment", n=1000, conversions=115),
            actual_duration_days=3,
            novelty_effect_days=7,
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Novelty Effect Risk")
        self.assertEqual(check.status, CheckStatus.WARN)
        self.assertEqual(check.evidence["actual_duration_days"], 3)

    def test_pass_when_duration_meets_threshold(self):
        exp = ExperimentSummary(
            experiment_id="full_run",
            metric_name="conversion",
            control=VariantSummary("control", n=5000, conversions=500),
            treatment=VariantSummary("treatment", n=5000, conversions=550),
            actual_duration_days=14,
            novelty_effect_days=7,
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Novelty Effect Risk")
        self.assertEqual(check.status, CheckStatus.PASS)

    def test_insufficient_input_when_duration_not_provided(self):
        exp = ExperimentSummary(
            experiment_id="no_duration",
            metric_name="conversion",
            control=VariantSummary("control", n=1000, conversions=100),
            treatment=VariantSummary("treatment", n=1000, conversions=110),
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Novelty Effect Risk")
        self.assertEqual(check.status, CheckStatus.INSUFFICIENT_INPUT)

    def test_custom_novelty_threshold(self):
        exp = ExperimentSummary(
            experiment_id="custom_threshold",
            metric_name="engagement",
            control=VariantSummary("control", n=2000, conversions=200),
            treatment=VariantSummary("treatment", n=2000, conversions=220),
            actual_duration_days=10,
            novelty_effect_days=14,
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Novelty Effect Risk")
        self.assertEqual(check.status, CheckStatus.WARN)
        self.assertEqual(check.evidence["novelty_effect_days"], 14)

    def test_exact_threshold_boundary_passes(self):
        exp = ExperimentSummary(
            experiment_id="boundary",
            metric_name="conversion",
            control=VariantSummary("control", n=3000, conversions=300),
            treatment=VariantSummary("treatment", n=3000, conversions=330),
            actual_duration_days=7,
            novelty_effect_days=7,
        )
        report = TrialCheck(exp).run()
        check = next(c for c in report.checks if c.check == "Novelty Effect Risk")
        self.assertEqual(check.status, CheckStatus.PASS)


if __name__ == "__main__":
    unittest.main()
