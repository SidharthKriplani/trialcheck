# TrialCheck Audit Report — checkout_copy_test_v0

**Metric:** checkout_conversion_rate
**Overall status:** `FAIL`

## Interpretation

Readout is not action-ready: 1 failure(s), 5 warning(s), and 1 insufficient-input check(s). Investigate failed checks before using the result.

## Checks

| Check | Status | Detail | Recommendation |
|---|---:|---|---|
| Sample Ratio Mismatch | `PASS` | Observed split 10000/9800; expected split 9900.0/9900.0. SRM chi-square=2.0202, p=0.155218. | No SRM detected under the configured alpha threshold. |
| Primary Metric Statistical Readout | `PASS` | Control rate=11.0000%; treatment rate=12.1020%; absolute lift=1.1020%; relative lift=10.02%; p=0.015261. | Primary metric is statistically distinguishable at the configured alpha; still review practical size, SRM, peeking, and guardrails. |
| Continuous Metric (Welch t-test) | `INSUFFICIENT_INPUT` | Mean and/or std not provided; continuous metric check skipped. | Supply mean, std, and n for both variants to enable Welch's t-test. |
| Practical Significance | `WARN` | Absolute lift=1.1020%; practical threshold=2.0000%. | The result may be statistically interesting but is smaller than the configured business threshold. |
| MDE Context | `WARN` | Observed absolute lift=1.1020%; planned MDE=5.0000%. | Observed movement is below the planned MDE; be careful treating this as a meaningful win. |
| Peeking / Early Readout Risk | `WARN` | 2 interim look(s) were reported. | Do not treat a conventional p-value as final unless the design accounted for early stopping or repeated looks. |
| Guardrail: refund_rate | `FAIL` | refund_rate control=0.021, treatment=0.028; movement=0.007; tolerance=0.003. | Guardrail increased beyond tolerance by 0.004; review before shipping. |
| Guardrail: revenue_per_user | `PASS` | revenue_per_user control=12.8, treatment=12.6; movement=-0.2; tolerance=0.5. | No harmful guardrail movement beyond the configured tolerance. |
| Pre-period Balance Summary | `WARN` | Checked 2 covariate(s); mean absolute SMD=0.1148; max absolute SMD=0.1967. | Review individual covariate rows for imbalance details. |
| Pre-period Balance: pre_period_orders_per_user | `PASS` | Standardized mean difference=0.0330; threshold=0.1000. | No material imbalance detected for this covariate under the configured SMD threshold. |
| Pre-period Balance: pre_period_revenue_per_user | `WARN` | Standardized mean difference=0.1967; threshold=0.1000. | Covariate imbalance detected; consider stratified analysis, regression adjustment, or platform assignment review. |

## Claim Boundary

TrialCheck audits common readout risks. It does not run experiments, prove causality, replace an experimentation platform, or make shipping decisions automatically.
