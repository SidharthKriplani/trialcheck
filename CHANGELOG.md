# Changelog

## [0.2.0] — 2025-05-05

### Added
- **Welch's t-test continuous metric check** (`continuous_metric_check`).  When
  `VariantSummary.mean` and `VariantSummary.std` are provided, TrialCheck now
  runs a Welch two-sample t-test (unequal variances) and emits `t_stat`, `dof`,
  and `p_value` in the evidence block.  Welch-Satterthwaite degrees of freedom
  are computed from first principles with no scipy dependency.  Python 3.12+
  uses `math.betainc` for exact t-distribution p-values; earlier versions fall
  back to the normal approximation (conservative for large dof, valid for n >
  30 per arm).
- **4-scenario demo** (`scripts/generate_demo_reports.py`).  Scenarios:
  `clean_pass`, `srm_fail`, `peeking_warn`, `guardrail_harm`.  Each writes
  JSON / Markdown / HTML output files.
- **GitHub Actions CI** (`.github/workflows/ci.yml`): matrix test across Python
  3.10, 3.11, 3.12 on every push and pull request.
- **GitHub Actions publish** (`.github/workflows/publish.yml`): trusted
  publisher OIDC release to PyPI on tagged release.
- **Expanded test suite** — 17 tests (up from 6): continuous metric pass/warn/
  skip/zero-std/evidence, edge cases for all existing checks, end-to-end
  `overall=PASS` scenario.

### Changed
- `auditor.py` version metadata bumped to `0.2.0`.
- `scripts/generate_demo_reports.py` rewritten to run all four canonical
  scenarios and preserve backward-compatible `trialcheck_report.*` outputs.
- `METHODOLOGY.md` updated to document Welch t-test and betainc fallback.

## [0.1.0] — 2025-04-20

Initial release.  Checks: SRM (chi-square df=1), primary metric two-proportion
z-test, practical significance, MDE context, peeking risk, guardrail movement,
pre-period covariate balance (SMD).  Zero dependencies.  JSON / Markdown / HTML
report rendering.
