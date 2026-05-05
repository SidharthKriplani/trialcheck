# TrialCheck Audit Report — checkout-ui-v2-guardrail

**Metric:** checkout_conversion_rate
**Overall status:** `FAIL`

## Interpretation

Readout is not action-ready: 2 failure(s), 0 warning(s), and 1 insufficient-input check(s). Investigate failed checks before using the result.

## Checks

| Check | Status | Detail | Recommendation |
|---|---:|---|---|
| Sample Ratio Mismatch | `PASS` | Observed split 15000/15000; expected split 15000.0/15000.0. SRM chi-square=0.0000, p=1.000000. | No SRM detected under the configured alpha threshold. |
| Primary Metric Statistical Readout | `PASS` | Control rate=9.0000%; treatment rate=10.2000%; absolute lift=1.2000%; relative lift=13.33%; p=0.000419. | Primary metric is statistically distinguishable at the configured alpha; still review practical size, SRM, peeking, and guardrails. |
| Continuous Metric (Welch t-test) | `PASS` | Control mean=4.82 ± 2.3 (n=15000); treatment mean=4.91 ± 2.28 (n=15000); absolute lift=0.09; Welch t=3.4036; dof=29995.7; p=0.000665. | Continuous metric is statistically distinguishable at the configured alpha; still review practical size, SRM, peeking, and guardrails. |
| Practical Significance | `PASS` | Absolute lift=1.2000%; practical threshold=0.8000%. | Observed movement meets the configured practical threshold. |
| MDE Context | `PASS` | Observed absolute lift=1.2000%; planned MDE=0.9000%. | Observed movement is at least as large as the planned MDE. |
| Peeking / Early Readout Risk | `PASS` | Actual duration was 100.0% of planned duration and no interim looks were reported. | No simple peeking warning detected from provided timing metadata. |
| Guardrail: revenue_per_user | `FAIL` | revenue_per_user control=4.82, treatment=4.61; movement=-0.21; tolerance=0.05. | Guardrail decreased beyond tolerance by 0.16; review before shipping. |
| Guardrail: refund_rate | `FAIL` | refund_rate control=0.02, treatment=0.038; movement=0.018; tolerance=0.005. | Guardrail increased beyond tolerance by 0.013; review before shipping. |
| Pre-period Balance | `INSUFFICIENT_INPUT` | No pre-period covariates were provided. | Provide pre-period covariate summaries when available, especially for high-impact experiments. |

## Claim Boundary

TrialCheck audits common readout risks. It does not run experiments, prove causality, replace an experimentation platform, or make shipping decisions automatically.
