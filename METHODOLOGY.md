# TrialCheck Methodology

TrialCheck v0.2 focuses on common experiment-readout failure modes that can be checked from summary data. All statistical computations use Python's standard library (`math`, `statistics`) with zero external dependencies.

## 1. Sample Ratio Mismatch

For a two-arm experiment, TrialCheck compares observed assignment counts against the expected split using a chi-square test with one degree of freedom.

If `p < alpha`, the SRM check fails. A failed SRM check means the experiment assignment, logging, exposure filtering, or data extraction should be investigated before interpreting the metric result.

## 2. Primary metric statistical readout

For binary conversion metrics, TrialCheck uses a two-proportion z-test. This is not a replacement for the source experimentation platform. It is a lightweight check for summary-level readouts.

## 3. Continuous metric (Welch's t-test)

When a primary metric is a mean rather than a conversion rate (e.g. revenue per user, session duration), TrialCheck runs Welch's two-sample t-test:

```text
t = (treatment_mean - control_mean) / sqrt(s_c²/n_c + s_t²/n_t)
```

Degrees of freedom are computed using the Welch-Satterthwaite equation:

```text
dof = (s_c²/n_c + s_t²/n_t)² / ((s_c²/n_c)²/(n_c-1) + (s_t²/n_t)²/(n_t-1))
```

Welch's t-test (not Student's t-test) is the correct default because the treatment may change metric variance, and assuming equal variances when they differ inflates Type I error.

**p-value computation**: Python 3.12+ uses `math.betainc` for an exact regularized incomplete beta function evaluation. Earlier Python versions fall back to the normal approximation via `math.erfc`, which is conservative for large degrees of freedom (valid when dof > 30).

The check returns `INSUFFICIENT_INPUT` and is skipped when `mean` or `std` are absent from either variant, so binary conversion experiments are unaffected.

## 4. Practical significance

A statistically significant result may still be too small to matter. TrialCheck compares observed absolute lift against a user-provided business threshold.

If the observed movement is below that threshold, the check returns `WARN`, not `FAIL`.

## 5. MDE context

TrialCheck compares observed absolute lift with the planned minimum detectable effect. If observed lift is below MDE, the result may be weaker than what the experiment was designed to detect.

This is context, not a formal retrospective power proof.

## 6. Peeking / early readout risk

TrialCheck flags simple peeking risk when:

- the actual duration is less than 70% of the planned duration, or
- interim looks are reported.

This is a heuristic warning. TrialCheck does not implement sequential testing.

## 7. Guardrail movement

Guardrails are supplied by the user with a harmful direction and tolerance. If movement exceeds the tolerance in the harmful direction, TrialCheck returns `FAIL`.

## 8. Pre-period balance

For pre-period covariates, TrialCheck computes standardized mean difference:

```text
SMD = (treatment_mean - control_mean) / pooled_standard_deviation
```

If absolute SMD exceeds the configured threshold, the covariate balance check returns `WARN`.

## Output semantics

- `PASS`: no issue detected under the configured threshold
- `WARN`: potential decision risk or missing context
- `FAIL`: serious readout risk that should be investigated before action
- `INSUFFICIENT_INPUT`: required data for this check was not provided

TrialCheck should be used as decision support, not as an automatic experiment decision-maker.
