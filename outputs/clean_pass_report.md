# TrialCheck Audit Report — checkout-ui-v2-clean

**Metric:** checkout_conversion_rate
**Overall status:** `PASS`

## Interpretation

Readout passed the configured v0 audit checks. This does not guarantee causal validity; it only means no configured warning was detected.

## Checks

| Check | Status | Detail | Recommendation |
|---|---:|---|---|
| Sample Ratio Mismatch | `PASS` | Observed split 15000/15000; expected split 15000.0/15000.0. SRM chi-square=0.0000, p=1.000000. | No SRM detected under the configured alpha threshold. |
| Primary Metric Statistical Readout | `PASS` | Control rate=9.0000%; treatment rate=10.2000%; absolute lift=1.2000%; relative lift=13.33%; p=0.000419. | Primary metric is statistically distinguishable at the configured alpha; still review practical size, SRM, peeking, and guardrails. |
| Continuous Metric (Welch t-test) | `PASS` | Control mean=4.82 ± 2.3 (n=15000); treatment mean=4.91 ± 2.28 (n=15000); absolute lift=0.09; Welch t=3.4036; dof=29995.7; p=0.000665. | Continuous metric is statistically distinguishable at the configured alpha; still review practical size, SRM, peeking, and guardrails. |
| Practical Significance | `PASS` | Absolute lift=1.2000%; practical threshold=0.8000%. | Observed movement meets the configured practical threshold. |
| MDE Context | `PASS` | Observed absolute lift=1.2000%; planned MDE=0.9000%. | Observed movement is at least as large as the planned MDE. |
| Peeking / Early Readout Risk | `PASS` | Actual duration was 100.0% of planned duration and no interim looks were reported. | No simple peeking warning detected from provided timing metadata. |
| Guardrail: revenue_per_user | `PASS` | revenue_per_user control=4.82, treatment=4.91; movement=0.09; tolerance=0.05. | No harmful guardrail movement beyond the configured tolerance. |
| Guardrail: support_contact_rate | `PASS` | support_contact_rate control=0.031, treatment=0.03; movement=-0.001; tolerance=0.005. | No harmful guardrail movement beyond the configured tolerance. |
| Pre-period Balance: past_orders | `PASS` | Standardized mean difference=-0.0042; threshold=0.1000. | No material imbalance detected for this covariate under the configured SMD threshold. |

## Claim Boundary

TrialCheck audits common readout risks. It does not run experiments, prove causality, replace an experimentation platform, or make shipping decisions automatically.
