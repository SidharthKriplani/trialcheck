# TrialCheck Audit Report — checkout-ui-v2-srm

**Metric:** checkout_conversion_rate
**Overall status:** `FAIL`

## Interpretation

Readout is not action-ready: 1 failure(s), 0 warning(s), and 3 insufficient-input check(s). Investigate failed checks before using the result.

## Checks

| Check | Status | Detail | Recommendation |
|---|---:|---|---|
| Sample Ratio Mismatch | `FAIL` | Observed split 14100/10900; expected split 12500.0/12500.0. SRM chi-square=409.6000, p=0.000000. | Investigate assignment, logging, or filtering before using this result. |
| Primary Metric Statistical Readout | `PASS` | Control rate=9.0000%; treatment rate=10.5046%; absolute lift=1.5046%; relative lift=16.72%; p=0.000065. | Primary metric is statistically distinguishable at the configured alpha; still review practical size, SRM, peeking, and guardrails. |
| Continuous Metric (Welch t-test) | `INSUFFICIENT_INPUT` | Mean and/or std not provided; continuous metric check skipped. | Supply mean, std, and n for both variants to enable Welch's t-test. |
| Practical Significance | `PASS` | Absolute lift=1.5046%; practical threshold=0.8000%. | Observed movement meets the configured practical threshold. |
| MDE Context | `PASS` | Observed absolute lift=1.5046%; planned MDE=0.9000%. | Observed movement is at least as large as the planned MDE. |
| Peeking / Early Readout Risk | `PASS` | Actual duration was 100.0% of planned duration and no interim looks were reported. | No simple peeking warning detected from provided timing metadata. |
| Guardrail Movement | `INSUFFICIENT_INPUT` | No guardrail metrics were provided. | Provide guardrails such as revenue per user, refund rate, latency, session quality, or support contacts before shipping decisions. |
| Pre-period Balance | `INSUFFICIENT_INPUT` | No pre-period covariates were provided. | Provide pre-period covariate summaries when available, especially for high-impact experiments. |

## Claim Boundary

TrialCheck audits common readout risks. It does not run experiments, prove causality, replace an experimentation platform, or make shipping decisions automatically.
