# EDEN Grid Sentinel — M4 Guardian & Human Approval Patch

**Deliverable date:** 2026-10-31. This ZIP is an overlay on top of the **complete M3 patch**, not a new GitHub repository or a replacement for M1/M2. No GitHub writes or live Meta calls have been performed.

## Contents

- New `src/eden/sentinel/m4_guardian.py`, `m4_workflow.py`, `m4_routes.py`, `m4_perception.py`.
- New `tests/sentinel/test_m4.py` and `scripts/m4_demo.py`.
- `src/eden/sentinel/api.py` with `m4_router` registration; `tests/sentinel/test_health.py` updated for the new routes. **Merge these two files manually if your M2/M3 API or tests differ.**
- Documentation: `docs/hackathon/M4_RUNBOOK.md`, `M4_REPORT.md`, `M4_RESULTS.json`, `M4_AGENT_PROMPT.md`.

## Recommended Git workflow

Do not branch from the empty M3 pointer before verifying actual M3 files are pushed. M3 must contain `m3_forecast.py`, `m3_scheduler.py`, `m3_routes.py` and passing tests. Once confirmed, from your local checkout:

```powershell
git fetch origin
git switch feat/m3-forecast-scheduler
git pull --ff-only origin feat/m3-forecast-scheduler
Test-Path src/eden/sentinel/m3_scheduler.py
# If False: apply/commit/push the prior M3 patch first; do not continue M4.
git switch -c feat/m4-guardian-human-approval
# Copy this ZIP's contents over the repository root, preserving directory paths.
# Merge api.py and test_health.py with existing branch edits, do not blindly replace them.
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[pipeline,dev]"
python -m pytest -q
python scripts/m4_demo.py --scenario critical_priority_school --operator demo-operator --apply-simulation
```

During the CLI demo, read the proposal, then type `approved` or `rejected` when prompted. The command always runs **simulation only**. After reviewing actual output, consider pushing the isolated branch and opening a **draft** PR; do not merge until owner acceptance and earlier milestone/rules checks.

```powershell
git diff --check
git status --short
git add src/eden/sentinel/api.py src/eden/sentinel/m4_*.py tests/sentinel/test_health.py tests/sentinel/test_m4.py scripts/m4_demo.py docs/hackathon/M4_*.md docs/hackathon/M4_RESULTS.json README_M4_PATCH.md
git commit -m "feat(m4): add guardian and local human approval workflow"
git push -u origin feat/m4-guardian-human-approval
gh pr create --draft --base feat/m3-forecast-scheduler --head feat/m4-guardian-human-approval --title "M4: Guardian and human approval (simulation only)" --body "Forecast-time Guardian validation, identified operator approval, expiring local proposals, audit chain, simulation-only apply, optional SAM request builder. CI and owner acceptance pending."
```

**Important:** Public Git history once included a populated Meta API credential. Verify revocation and replacement, and do not copy or print any keys. M4 does not need a Meta API key.

Read `M4_RUNBOOK.md` and `M4_REPORT.md` before publishing. These include all limitations, especially the default-disabled, local-only demo API and the lack of actual SAM inference.
