"""Report rendering helpers for TrialCheck."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Union

from .models import TrialReport


PathLike = Union[str, Path]


def to_json(report: TrialReport, indent: int = 2) -> str:
    return json.dumps(report.to_dict(), indent=indent, sort_keys=False)


def to_markdown(report: TrialReport) -> str:
    lines = [
        f"# TrialCheck Audit Report — {report.experiment_id}",
        "",
        f"**Metric:** {report.metric_name}",
        f"**Overall status:** `{report.overall_status.value}`",
        "",
        "## Interpretation",
        "",
        report.interpretation,
        "",
        "## Checks",
        "",
        "| Check | Status | Detail | Recommendation |",
        "|---|---:|---|---|",
    ]
    for check in report.checks:
        lines.append(
            f"| {check.check} | `{check.status.value}` | {check.detail} | {check.recommendation} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "TrialCheck audits common readout risks. It does not run experiments, prove causality, replace an experimentation platform, or make shipping decisions automatically.",
            "",
        ]
    )
    return "\n".join(lines)


def to_html(report: TrialReport) -> str:
    rows = []
    for check in report.checks:
        rows.append(
            "<tr>"
            f"<td>{html.escape(check.check)}</td>"
            f"<td><code>{html.escape(check.status.value)}</code></td>"
            f"<td>{html.escape(check.detail)}</td>"
            f"<td>{html.escape(check.recommendation)}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TrialCheck Audit Report — {html.escape(report.experiment_id)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 40px; color: #172033; }}
    .card {{ border: 1px solid #d7dce5; border-radius: 16px; padding: 24px; max-width: 1100px; box-shadow: 0 8px 24px rgba(20,30,50,.08); }}
    h1 {{ margin-top: 0; }}
    .status {{ display: inline-block; padding: 6px 10px; border-radius: 999px; background: #f2f4f8; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border-bottom: 1px solid #e8ebf1; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f8fafc; }}
    code {{ font-weight: 700; }}
    .boundary {{ margin-top: 24px; padding: 14px; border-radius: 12px; background: #fff8e7; }}
  </style>
</head>
<body>
  <main class="card">
    <h1>TrialCheck Audit Report</h1>
    <p><strong>Experiment:</strong> {html.escape(report.experiment_id)}</p>
    <p><strong>Metric:</strong> {html.escape(report.metric_name)}</p>
    <p><strong>Overall status:</strong> <span class="status">{html.escape(report.overall_status.value)}</span></p>
    <h2>Interpretation</h2>
    <p>{html.escape(report.interpretation)}</p>
    <h2>Checks</h2>
    <table>
      <thead><tr><th>Check</th><th>Status</th><th>Detail</th><th>Recommendation</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    <div class="boundary"><strong>Claim boundary:</strong> TrialCheck audits common readout risks. It does not run experiments, prove causality, replace an experimentation platform, or make shipping decisions automatically.</div>
  </main>
</body>
</html>"""


def write_report(report: TrialReport, path: PathLike) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".json":
        path.write_text(to_json(report), encoding="utf-8")
    elif suffix in {".md", ".markdown"}:
        path.write_text(to_markdown(report), encoding="utf-8")
    elif suffix in {".html", ".htm"}:
        path.write_text(to_html(report), encoding="utf-8")
    else:
        raise ValueError("Unsupported report extension. Use .json, .md, or .html")
