# M3 Forecast + Scheduling Patch (October 31, 2026)

**Repository:** https://github.com/Edensystems/eden-grid-sentinel-meta-2026

**Expected starting point:** `feat/m1-microgrid-digital-twin`, commit `aa3cf08ffc22471f3407d99f300dcaf70f5ddd64` (draft PR #1). M2 was not published to GitHub when this package was assembled; it can be integrated independently without overwriting its `muse.py` adapter.

This is an **overlay, not an independent repository**. Copy its contents into the existing M1 checkout. New files are `m3_*.py`, `tests/sentinel/test_m3.py`, `scripts/m3_demo.py` and M3 docs. Two existing M1 files change: `src/eden/sentinel/api.py` adds an M3 simulation-only router; `tests/sentinel/test_health.py` includes the newly allowed read-only paths. If you have later API edits, merge those two files manually.

## Windows PowerShell setup

```powershell
git fetch origin
git switch feat/m1-microgrid-digital-twin
git pull --ff-only origin feat/m1-microgrid-digital-twin
git switch -c feat/m3-forecast-scheduler
# Unzip/copy the patch OVER the root of the current Git checkout, preserving paths.
git diff --check
git status --short
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[pipeline,dev]"
python -m pytest -q
python scripts/m3_demo.py --scenario critical_priority_school
python -m uvicorn eden.sentinel.api:app --port 8000
```

In another terminal: `Invoke-RestMethod http://127.0.0.1:8000/m3/scenarios` and `Invoke-RestMethod http://127.0.0.1:8000/m3/evaluate/critical_priority_school`.

Review actual test output and diffs first. If approved for a **draft PR only**:

```powershell
git add src/eden/sentinel/api.py src/eden/sentinel/m3_*.py tests/sentinel/test_health.py tests/sentinel/test_m3.py scripts/m3_demo.py docs/hackathon/M3_*.md docs/hackathon/M3_RESULTS.json README_M3_PATCH.md
git commit -m "feat(m3): forecast-driven constrained load scheduling"
git push -u origin feat/m3-forecast-scheduler
gh pr create --draft --base feat/m1-microgrid-digital-twin --head feat/m3-forecast-scheduler --title "M3: forecasting and constrained scheduling" --body "Synthetic forecast-driven planning, held-out realized evaluation, safety checks and tests. Draft: approval gates pending."
```

**Do not make live model calls or deploy.** Review hackathon eligibility and provenance. The public Git history previously exposed a Meta key; revoke/rotate it if not already done and never republish it. M3 cannot be marked complete before full-repository supported-Python CI and explicit owner acceptance.
