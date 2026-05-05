"""Small CLI for generating demo reports."""

from __future__ import annotations

import argparse
from pathlib import Path

from .auditor import TrialCheck
from .io import load_experiment_json
from .reporting import write_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a TrialCheck audit from a JSON experiment summary.")
    parser.add_argument("input", type=Path, help="Path to experiment summary JSON")
    parser.add_argument("--out", type=Path, default=Path("outputs/trialcheck_report.md"), help="Output report path: .json, .md, or .html")
    args = parser.parse_args()

    experiment = load_experiment_json(args.input)
    report = TrialCheck(experiment).run()
    write_report(report, args.out)
    print(f"Wrote {args.out}")
    print(f"Overall status: {report.overall_status.value}")


if __name__ == "__main__":
    main()
