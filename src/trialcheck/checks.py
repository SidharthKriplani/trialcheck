"""Audit checks for completed A/B experiment readouts."""

from __future__ import annotations

import math
from statistics import mean
from typing import List

from .models import CheckResult, CheckStatus, ExperimentSummary, GuardrailMetric, PrePeriodCovariate
from .stats import chi_square_df1_survival, two_proportion_z_test, welch_t_test


def minimum_sample_size_check(exp: ExperimentSummary) -> CheckResult:
    """Warn when either variant's sample size falls below the configured minimum."""
    min_n = exp.min_sample_size
    n_c, n_t = exp.control.n, exp.treatment.n
    if n_c < min_n or n_t < min_n:
        return CheckResult(
            check="Minimum Sample Size",
            status=CheckStatus.WARN,
            detail=(
                f"Control n={n_c}, treatment n={n_t}; minimum threshold={min_n}. "
                "Small samples inflate variance and produce unreliable p-values."
            ),
            recommendation=(
                "Continue the experiment until both variants reach the minimum sample size "
                "required for the configured MDE and alpha."
            ),
            evidence={"n_control": n_c, "n_treatment": n_t, "min_n_threshold": min_n},
        )
    return CheckResult(
        check="Minimum Sample Size",
        status=CheckStatus.PASS,
        detail=f"Control n={n_c}, treatment n={n_t}; both meet the minimum threshold of {min_n}.",
        recommendation="Sample sizes meet the minimum threshold.",
        evidence={"n_control": n_c, "n_treatment": n_t, "min_n_threshold": min_n},
    )


def novelty_effect_check(exp: ExperimentSummary) -> CheckResult:
    """Warn when experiment runtime is shorter than the novelty-effect washout window."""
    if exp.actual_duration_days is None:
        return CheckResult(
            check="Novelty Effect Risk",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="actual_duration_days not provided; novelty effect cannot be assessed.",
            recommendation="Provide actual_duration_days to enable this check.",
        )
    threshold = exp.novelty_effect_days
    days = exp.actual_duration_days
    if days < threshold:
        return CheckResult(
            check="Novelty Effect Risk",
            status=CheckStatus.WARN,
            detail=(
                f"Experiment ran for {days} day(s); novelty washout threshold is {threshold} day(s). "
                "Early uplift may reflect user curiosity rather than sustained behaviour change."
            ),
            recommendation=(
                f"Allow at least {threshold} days before reading out to reduce novelty-effect bias. "
                "Consider re-checking metrics after novelty effects dissipate."
            ),
            evidence={"actual_duration_days": days, "novelty_effect_days": threshold},
        )
    return CheckResult(
        check="Novelty Effect Risk",
        status=CheckStatus.PASS,
        detail=f"Experiment ran for {days} day(s), meeting the {threshold}-day novelty washout window.",
        recommendation="No novelty-effect risk detected under the configured threshold.",
        evidence={"actual_duration_days": days, "novelty_effect_days": threshold},
    )


def srm_check(exp: ExperimentSummary) -> CheckResult:
    total = exp.control.n + exp.treatment.n
    if total <= 0:
        return CheckResult(
            check="Sample Ratio Mismatch",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="No assignment counts were provided.",
            recommendation="Provide control and treatment sample sizes before interpreting the readout.",
        )
    if not (0 < exp.expected_control_ratio < 1):
        return CheckResult(
            check="Sample Ratio Mismatch",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="Expected control ratio must be between 0 and 1.",
            recommendation="Set the planned randomization split, for example 0.5 for a 50/50 test.",
        )

    expected_control = total * exp.expected_control_ratio
    expected_treatment = total * (1 - exp.expected_control_ratio)
    chi2 = ((exp.control.n - expected_control) ** 2 / expected_control) + (
        (exp.treatment.n - expected_treatment) ** 2 / expected_treatment
    )
    p_value = chi_square_df1_survival(chi2)
    status = CheckStatus.FAIL if p_value < exp.alpha else CheckStatus.PASS
    detail = (
        f"Observed split {exp.control.n}/{exp.treatment.n}; expected split "
        f"{expected_control:.1f}/{expected_treatment:.1f}. SRM chi-square={chi2:.4f}, p={p_value:.6f}."
    )
    recommendation = (
        "Investigate assignment, logging, or filtering before using this result."
        if status == CheckStatus.FAIL
        else "No SRM detected under the configured alpha threshold."
    )
    return CheckResult(
        check="Sample Ratio Mismatch",
        status=status,
        detail=detail,
        recommendation=recommendation,
        evidence={
            "control_n": exp.control.n,
            "treatment_n": exp.treatment.n,
            "expected_control_ratio": exp.expected_control_ratio,
            "chi_square": round(chi2, 6),
            "p_value": round(p_value, 8),
            "alpha": exp.alpha,
        },
    )


def primary_metric_check(exp: ExperimentSummary) -> CheckResult:
    control_rate = exp.control.rate()
    treatment_rate = exp.treatment.rate()
    if control_rate is None or treatment_rate is None:
        return CheckResult(
            check="Primary Metric Statistical Readout",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="Conversion counts were not provided for both variants.",
            recommendation="Provide conversions and sample sizes for a two-proportion readout, or extend the package with a continuous metric adapter.",
        )

    z_stat, p_value = two_proportion_z_test(
        exp.control.conversions or 0,
        exp.control.n,
        exp.treatment.conversions or 0,
        exp.treatment.n,
    )
    absolute_lift = treatment_rate - control_rate
    relative_lift = absolute_lift / control_rate if control_rate else math.nan
    if p_value is None:
        status = CheckStatus.INSUFFICIENT_INPUT
        detail = "Unable to compute a valid two-proportion z-test."
        recommendation = "Check that both variants have positive sample sizes and valid conversion counts."
    else:
        status = CheckStatus.PASS if p_value < exp.alpha else CheckStatus.WARN
        detail = (
            f"Control rate={control_rate:.4%}; treatment rate={treatment_rate:.4%}; "
            f"absolute lift={absolute_lift:.4%}; relative lift={relative_lift:.2%}; p={p_value:.6f}."
        )
        recommendation = (
            "Primary metric is statistically distinguishable at the configured alpha; still review practical size, SRM, peeking, and guardrails."
            if status == CheckStatus.PASS
            else "Primary metric is not statistically distinguishable at the configured alpha; avoid over-reading the observed lift."
        )
    return CheckResult(
        check="Primary Metric Statistical Readout",
        status=status,
        detail=detail,
        recommendation=recommendation,
        evidence={
            "control_rate": round(control_rate, 8),
            "treatment_rate": round(treatment_rate, 8),
            "absolute_lift": round(absolute_lift, 8),
            "relative_lift": None if math.isnan(relative_lift) else round(relative_lift, 8),
            "z_stat": None if z_stat is None else round(z_stat, 6),
            "p_value": None if p_value is None else round(p_value, 8),
            "alpha": exp.alpha,
        },
    )


def continuous_metric_check(exp: ExperimentSummary) -> CheckResult:
    """Welch's t-test for continuous primary metrics (mean/std inputs).

    Used when the primary metric is a mean (e.g. revenue per user, session
    duration) rather than a conversion rate.  Skipped automatically when
    mean/std are not provided.
    """
    c_mean = exp.control.mean
    t_mean = exp.treatment.mean
    c_std = exp.control.std
    t_std = exp.treatment.std
    c_n = exp.control.n
    t_n = exp.treatment.n

    if any(v is None for v in (c_mean, t_mean, c_std, t_std)):
        return CheckResult(
            check="Continuous Metric (Welch t-test)",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="Mean and/or std not provided; continuous metric check skipped.",
            recommendation="Supply mean, std, and n for both variants to enable Welch's t-test.",
        )

    t_stat, dof, p_value = welch_t_test(c_mean, c_std, c_n, t_mean, t_std, t_n)  # type: ignore[arg-type]
    if t_stat is None or p_value is None:
        return CheckResult(
            check="Continuous Metric (Welch t-test)",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="Could not compute Welch's t-test; check that n > 1 and std >= 0 for both variants.",
            recommendation="Verify that variant sample sizes are at least 2 and standard deviations are non-negative.",
        )

    absolute_lift = t_mean - c_mean  # type: ignore[operator]
    relative_lift = absolute_lift / c_mean if c_mean else math.nan
    status = CheckStatus.PASS if p_value < exp.alpha else CheckStatus.WARN
    detail = (
        f"Control mean={c_mean:.6g} ± {c_std:.6g} (n={c_n}); "
        f"treatment mean={t_mean:.6g} ± {t_std:.6g} (n={t_n}); "
        f"absolute lift={absolute_lift:.6g}; Welch t={t_stat:.4f}; "
        f"dof={dof:.1f}; p={p_value:.6f}."
    )
    recommendation = (
        "Continuous metric is statistically distinguishable at the configured alpha; "
        "still review practical size, SRM, peeking, and guardrails."
        if status == CheckStatus.PASS
        else "Continuous metric difference is not statistically distinguishable at the configured alpha."
    )
    return CheckResult(
        check="Continuous Metric (Welch t-test)",
        status=status,
        detail=detail,
        recommendation=recommendation,
        evidence={
            "control_mean": c_mean,
            "treatment_mean": t_mean,
            "absolute_lift": round(absolute_lift, 8),
            "relative_lift": None if math.isnan(relative_lift) else round(relative_lift, 8),
            "t_stat": round(t_stat, 6),
            "dof": round(dof, 2),
            "p_value": round(p_value, 8),
            "alpha": exp.alpha,
        },
    )


def practical_significance_check(exp: ExperimentSummary) -> CheckResult:
    control_rate = exp.control.rate()
    treatment_rate = exp.treatment.rate()
    if control_rate is None or treatment_rate is None:
        return CheckResult(
            check="Practical Significance",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="Conversion rates could not be calculated.",
            recommendation="Provide conversion counts for both variants.",
        )
    if exp.practical_threshold is None:
        return CheckResult(
            check="Practical Significance",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="No practical significance threshold was provided.",
            recommendation="Provide the minimum absolute metric movement that is meaningful for the business.",
            evidence={"absolute_lift": round(treatment_rate - control_rate, 8)},
        )

    absolute_lift = treatment_rate - control_rate
    meets_threshold = abs(absolute_lift) >= exp.practical_threshold
    status = CheckStatus.PASS if meets_threshold else CheckStatus.WARN
    detail = (
        f"Absolute lift={absolute_lift:.4%}; practical threshold={exp.practical_threshold:.4%}."
    )
    recommendation = (
        "Observed movement meets the configured practical threshold."
        if meets_threshold
        else "The result may be statistically interesting but is smaller than the configured business threshold."
    )
    return CheckResult(
        check="Practical Significance",
        status=status,
        detail=detail,
        recommendation=recommendation,
        evidence={
            "absolute_lift": round(absolute_lift, 8),
            "practical_threshold": exp.practical_threshold,
            "meets_threshold": meets_threshold,
        },
    )


def mde_context_check(exp: ExperimentSummary) -> CheckResult:
    control_rate = exp.control.rate()
    treatment_rate = exp.treatment.rate()
    if control_rate is None or treatment_rate is None:
        return CheckResult(
            check="MDE Context",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="Conversion rates could not be calculated.",
            recommendation="Provide conversion counts for both variants.",
        )
    if exp.mde is None:
        return CheckResult(
            check="MDE Context",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="No minimum detectable effect was provided.",
            recommendation="Provide the planned MDE from the experiment plan to contextualize the observed effect.",
            evidence={"absolute_lift": round(treatment_rate - control_rate, 8)},
        )

    absolute_lift = treatment_rate - control_rate
    if abs(absolute_lift) >= exp.mde:
        status = CheckStatus.PASS
        recommendation = "Observed movement is at least as large as the planned MDE."
    else:
        status = CheckStatus.WARN
        recommendation = "Observed movement is below the planned MDE; be careful treating this as a meaningful win."
    return CheckResult(
        check="MDE Context",
        status=status,
        detail=f"Observed absolute lift={absolute_lift:.4%}; planned MDE={exp.mde:.4%}.",
        recommendation=recommendation,
        evidence={"absolute_lift": round(absolute_lift, 8), "mde": exp.mde},
    )


def peeking_risk_check(exp: ExperimentSummary) -> CheckResult:
    if exp.planned_duration_days is None or exp.actual_duration_days is None:
        return CheckResult(
            check="Peeking / Early Readout Risk",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="Planned and/or actual experiment duration was not provided.",
            recommendation="Provide planned and actual duration. If the experiment had repeated interim looks, report that explicitly.",
        )
    if exp.planned_duration_days <= 0 or exp.actual_duration_days <= 0:
        return CheckResult(
            check="Peeking / Early Readout Risk",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="Experiment duration values must be positive.",
            recommendation="Check planned_duration_days and actual_duration_days inputs.",
        )

    completion_ratio = exp.actual_duration_days / exp.planned_duration_days
    risky_duration = completion_ratio < 0.70
    risky_looks = exp.interim_looks > 0
    if risky_duration or risky_looks:
        status = CheckStatus.WARN
        reasons = []
        if risky_duration:
            reasons.append(f"actual duration was {completion_ratio:.1%} of planned duration")
        if risky_looks:
            reasons.append(f"{exp.interim_looks} interim look(s) were reported")
        detail = "; ".join(reasons) + "."
        recommendation = "Do not treat a conventional p-value as final unless the design accounted for early stopping or repeated looks."
    else:
        status = CheckStatus.PASS
        detail = f"Actual duration was {completion_ratio:.1%} of planned duration and no interim looks were reported."
        recommendation = "No simple peeking warning detected from provided timing metadata."
    return CheckResult(
        check="Peeking / Early Readout Risk",
        status=status,
        detail=detail,
        recommendation=recommendation,
        evidence={
            "planned_duration_days": exp.planned_duration_days,
            "actual_duration_days": exp.actual_duration_days,
            "completion_ratio": round(completion_ratio, 6),
            "interim_looks": exp.interim_looks,
        },
    )


def _check_one_guardrail(metric: GuardrailMetric) -> CheckResult:
    movement = metric.treatment_value - metric.control_value
    direction = metric.bad_direction.lower().strip()
    if direction not in {"increase", "decrease"}:
        return CheckResult(
            check=f"Guardrail: {metric.name}",
            status=CheckStatus.INSUFFICIENT_INPUT,
            detail="bad_direction must be either 'increase' or 'decrease'.",
            recommendation="Set bad_direction based on which movement is harmful for this guardrail.",
        )

    if direction == "increase":
        breach = movement > metric.tolerance
        harmful_phrase = "increased"
        harmful_amount = movement
    else:
        breach = -movement > metric.tolerance
        harmful_phrase = "decreased"
        harmful_amount = -movement

    status = CheckStatus.FAIL if breach else CheckStatus.PASS
    detail = (
        f"{metric.name} control={metric.control_value:.6g}, treatment={metric.treatment_value:.6g}; "
        f"movement={movement:.6g}; tolerance={metric.tolerance:.6g}."
    )
    recommendation = (
        f"Guardrail {harmful_phrase} beyond tolerance by {harmful_amount - metric.tolerance:.6g}; review before shipping."
        if breach
        else "No harmful guardrail movement beyond the configured tolerance."
    )
    return CheckResult(
        check=f"Guardrail: {metric.name}",
        status=status,
        detail=detail,
        recommendation=recommendation,
        evidence={
            "control_value": metric.control_value,
            "treatment_value": metric.treatment_value,
            "movement": movement,
            "bad_direction": direction,
            "tolerance": metric.tolerance,
            "unit": metric.unit,
        },
    )


def guardrail_checks(exp: ExperimentSummary) -> List[CheckResult]:
    if not exp.guardrails:
        return [
            CheckResult(
                check="Guardrail Movement",
                status=CheckStatus.INSUFFICIENT_INPUT,
                detail="No guardrail metrics were provided.",
                recommendation="Provide guardrails such as revenue per user, refund rate, latency, session quality, or support contacts before shipping decisions.",
            )
        ]
    return [_check_one_guardrail(metric) for metric in exp.guardrails]


def _standardized_mean_difference(covariate: PrePeriodCovariate) -> float:
    pooled_sd = math.sqrt((covariate.control_std**2 + covariate.treatment_std**2) / 2.0)
    if pooled_sd == 0:
        return 0.0 if covariate.control_mean == covariate.treatment_mean else math.inf
    return (covariate.treatment_mean - covariate.control_mean) / pooled_sd


def pre_period_balance_checks(exp: ExperimentSummary) -> List[CheckResult]:
    if not exp.pre_period_covariates:
        return [
            CheckResult(
                check="Pre-period Balance",
                status=CheckStatus.INSUFFICIENT_INPUT,
                detail="No pre-period covariates were provided.",
                recommendation="Provide pre-period covariate summaries when available, especially for high-impact experiments.",
            )
        ]

    rows: List[CheckResult] = []
    abs_smds = []
    for covariate in exp.pre_period_covariates:
        smd = _standardized_mean_difference(covariate)
        abs_smd = abs(smd)
        abs_smds.append(abs_smd)
        status = CheckStatus.WARN if abs_smd > covariate.max_abs_smd else CheckStatus.PASS
        rows.append(
            CheckResult(
                check=f"Pre-period Balance: {covariate.name}",
                status=status,
                detail=(
                    f"Standardized mean difference={smd:.4f}; threshold={covariate.max_abs_smd:.4f}."
                ),
                recommendation=(
                    "Covariate imbalance detected; consider stratified analysis, regression adjustment, or platform assignment review."
                    if status == CheckStatus.WARN
                    else "No material imbalance detected for this covariate under the configured SMD threshold."
                ),
                evidence={
                    "control_mean": covariate.control_mean,
                    "treatment_mean": covariate.treatment_mean,
                    "control_std": covariate.control_std,
                    "treatment_std": covariate.treatment_std,
                    "smd": None if math.isinf(smd) else round(smd, 8),
                    "max_abs_smd": covariate.max_abs_smd,
                },
            )
        )

    if len(rows) > 1:
        rows.insert(
            0,
            CheckResult(
                check="Pre-period Balance Summary",
                status=CheckStatus.WARN if any(x > 0.10 for x in abs_smds) else CheckStatus.PASS,
                detail=f"Checked {len(abs_smds)} covariate(s); mean absolute SMD={mean(abs_smds):.4f}; max absolute SMD={max(abs_smds):.4f}.",
                recommendation="Review individual covariate rows for imbalance details.",
                evidence={"covariate_count": len(abs_smds), "max_abs_smd": round(max(abs_smds), 8)},
            ),
        )
    return rows
