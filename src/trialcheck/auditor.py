"""Main TrialCheck auditor interface."""

from __future__ import annotations

from typing import Iterable, List

from .checks import (
    continuous_metric_check,
    guardrail_checks,
    mde_context_check,
    minimum_sample_size_check,
    novelty_effect_check,
    peeking_risk_check,
    practical_significance_check,
    pre_period_balance_checks,
    primary_metric_check,
    srm_check,
)
from .models import CheckResult, CheckStatus, ExperimentSummary, TrialReport


_STATUS_RANK = {
    CheckStatus.PASS: 0,
    CheckStatus.INSUFFICIENT_INPUT: 1,
    CheckStatus.WARN: 2,
    CheckStatus.FAIL: 3,
}


class TrialCheck:
    """Platform-agnostic A/B readout auditor.

    TrialCheck does not run experiments. It audits completed readouts from any
    experiment platform, spreadsheet, or warehouse export.
    """

    def __init__(self, experiment: ExperimentSummary):
        self.experiment = experiment

    def run(self) -> TrialReport:
        checks: List[CheckResult] = [
            minimum_sample_size_check(self.experiment),
            srm_check(self.experiment),
            primary_metric_check(self.experiment),
            continuous_metric_check(self.experiment),
            practical_significance_check(self.experiment),
            mde_context_check(self.experiment),
            peeking_risk_check(self.experiment),
            novelty_effect_check(self.experiment),
        ]
        checks.extend(guardrail_checks(self.experiment))
        checks.extend(pre_period_balance_checks(self.experiment))

        overall = self._overall_status(checks)
        interpretation = self._interpretation(overall, checks)
        return TrialReport(
            experiment_id=self.experiment.experiment_id,
            metric_name=self.experiment.metric_name,
            overall_status=overall,
            checks=checks,
            interpretation=interpretation,
            metadata={
                "tool": "trialcheck",
                "version": "0.2.0",
                "claim_boundary": "Audit helper only; does not guarantee causal validity or make shipping decisions.",
            },
        )

    @staticmethod
    def _overall_status(checks: Iterable[CheckResult]) -> CheckStatus:
        checks = list(checks)
        if any(check.status == CheckStatus.FAIL for check in checks):
            return CheckStatus.FAIL
        if any(check.status == CheckStatus.WARN for check in checks):
            return CheckStatus.WARN
        if any(check.status == CheckStatus.INSUFFICIENT_INPUT for check in checks):
            return CheckStatus.WARN
        return CheckStatus.PASS

    @staticmethod
    def _interpretation(overall: CheckStatus, checks: List[CheckResult]) -> str:
        fail_count = sum(check.status == CheckStatus.FAIL for check in checks)
        warn_count = sum(check.status == CheckStatus.WARN for check in checks)
        missing_count = sum(check.status == CheckStatus.INSUFFICIENT_INPUT for check in checks)
        if overall == CheckStatus.FAIL:
            return (
                f"Readout is not action-ready: {fail_count} failure(s), {warn_count} warning(s), "
                f"and {missing_count} insufficient-input check(s). Investigate failed checks before using the result."
            )
        if overall == CheckStatus.WARN:
            return (
                f"Readout requires caution: {warn_count} warning(s) and {missing_count} insufficient-input check(s). "
                "Treat the result as decision-support, not a ship/no-ship command."
            )
        return "Readout passed the configured v0 audit checks. This does not guarantee causal validity; it only means no configured warning was detected."
