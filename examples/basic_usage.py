from pathlib import Path

from trialcheck import TrialCheck, write_report
from trialcheck.io import load_experiment_json

ROOT = Path(__file__).resolve().parents[1]
experiment = load_experiment_json(ROOT / "sample_data" / "checkout_experiment_summary.json")
report = TrialCheck(experiment).run()

print(report.overall_status.value)
print(report.interpretation)

write_report(report, ROOT / "outputs" / "trialcheck_report.json")
write_report(report, ROOT / "outputs" / "trialcheck_report.md")
write_report(report, ROOT / "outputs" / "trialcheck_report.html")
