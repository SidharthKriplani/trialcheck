# Validation Summary

Validated locally with:

```bash
cd trialcheck_v0
set -e
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/generate_demo_reports.py
```

Result:

- Unit tests: 17/17 passing (TrialCheckTests: 6, ContinuousMetricTests: 5, EdgeCaseTests: 6)
- Demo scenarios: clean_pass=PASS, srm_fail=FAIL, peeking_warn=WARN, guardrail_harm=FAIL
- Canonical checkout experiment overall status: FAIL (deliberately breached refund-rate guardrail, peeking risk, effect below planned MDE)
