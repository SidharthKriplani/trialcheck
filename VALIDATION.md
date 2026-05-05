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

- Unit tests: 6/6 passing
- Demo reports generated: JSON, Markdown, HTML
- Example overall status: FAIL, due to a deliberately breached refund-rate guardrail and multiple WARN-level readout risks
