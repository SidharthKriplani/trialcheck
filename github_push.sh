#!/bin/bash
set -e
cd "$(dirname "$0")"

# Remove any stale lock from Claude's git init attempt
rm -f .git/index.lock 2>/dev/null || true

# If .git already exists from Claude's init, clean it up and start fresh
if [ -d .git ]; then
  rm -rf .git
fi

git init
git branch -m main
git config user.email "claudesubscription12@gmail.com"
git config user.name "Sidharth Kriplani"
git add -A
git commit -m "feat: TrialCheck v0.2.0

- Welch t-test continuous metric check (Welch-Satterthwaite dof, zero deps)
- 4-scenario demo: clean_pass, srm_fail, peeking_warn, guardrail_harm
- GitHub Actions CI matrix (Python 3.10/3.11/3.12) + PyPI publish workflow
- 17 tests (up from 6): ContinuousMetricTests (5) + EdgeCaseTests (6)
- TrialCheck_Interview_Defense.pdf
- CHANGELOG.md, updated METHODOLOGY.md + README, pyproject.toml -> 0.2.0
"
git remote add origin https://github.com/SidharthKriplani/trialcheck.git
git push -u origin main
