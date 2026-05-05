# TrialCheck Audit Report — checkout-ui-v2-peeking

**Metric:** checkout_conversion_rate
**Overall status:** `WARN`

## Interpretation

Readout requires caution: 1 warning(s) and 2 insufficient-input check(s). Treat the result as decision-support, not a ship/no-ship command.

## Checks

| Check | Status | Detail | Recommendation |
|---|---:|---|---|
| Sample Ratio Mismatch | `PASS` | Observed split 5800/5800; expected split 5800.0/5800.0. SRM chi-square=0.0000, p=1.000000. | No SRM detected under the configured alpha threshold. |
| Primary Metric Statistical Readout | `PASS` | Control rate=9.0000%; treatment rate=10.3966%; absolute lift=1.3966%; relative lift=15.52%; p=0.011043. | Primary metric is statistically distinguishable at the configured alpha; still review practical size, SRM, peeking, and guardrails. |
| Continuous Metric (Welch t-test) | `INSUFFICIENT_INPUT` | Mean and/or std not provided; continuous metric check skipped. | Supply mean, std, and n for both variants to enable Welch's t-test. |
| Practical Significance | `PASS` | Absolute lift=1.3966%; practical threshold=0.8000%. | Observed movement meets the configured practical threshold. |
| MDE Context | `PASS` | Observed absolute lift=1.3966%; planned MDE=0.9000%. | Observed movement is at least as large as the planned MDE. |
| Peeking / Early Readout Risk | `WARN` | actual duration was 35.7% of planned duration; 2 interim look(s) were reported. | Do not treat a conventional p-value as final unless the design accounted for early stopping or repeated looks. |
| Guardrail: revenue_per_user | `PASS` | revenue_per_user control=4.82, treatment=4.78; movement=-0.04; tolerance=0.05. | No harmful guardrail movement beyond the configured tolerance. |
| Pre-period Balance | `INSUFFICIENT_INPUT` | No pre-period covariates were provided. | Provide pre-period covariate summaries when available, especially for high-impact experiments. |

## Claim Boundary

TrialCheck audits common readout risks. It does not run experiments, prove causality, replace an experimentation platform, or make shipping decisions automatically.
