# EDEN Grid Sentinel M1 — Repository patch

Applied and reconciled locally on `feat/m1-microgrid-digital-twin` on 2026-10-30,
using current main `4422e9d1c16e6c7e4e5903efc5e1861659f4cc08`. The steps below
describe the original archive. Do not recopy its older M0 schema/report over the
verified integration. See `docs/hackathon/M1_REPORT.md` for current supported-Python
results, publication status and owner gates; `M1_RESULTS.json` contains exact synthetic summaries.

Use this archive against the original public repo at https://github.com/Edensystems/eden-grid-sentinel-meta-2026. It includes **only changed/new files**, not the entire original repository. It has not been pushed to GitHub because the integration returned HTTP 403 on branch creation.

## Apply

1. `git clone https://github.com/Edensystems/eden-grid-sentinel-meta-2026.git`
2. `cd eden-grid-sentinel-meta-2026`
3. `git checkout -b feat/m1-microgrid-digital-twin`
4. Extract the archive and copy the **contents** of its `eden-m1-patch` directory into the repository root, preserving paths and replacing `api.py`, `schemas.py`, `test_health.py`, and the stale `docs/hackathon/M0_REPORT.md`. The other files are additions. Do not replace the repository with the archive.
5. Run `py -3.12 -m venv .venv`, activate it, `pip install -e ".[pipeline,dev]"`, and `python -m pytest -q`.
6. Run the simulator with `python -m uvicorn eden.sentinel.api:app --reload`, test `/sim/scenarios` and `/sim/scenarios/night_reserve`.
7. Read `docs/hackathon/M1_RUNBOOK.md` and update `M1_REPORT.md` with actual results.
8. `git add src/eden/sentinel/api.py src/eden/sentinel/schemas.py src/eden/sentinel/twin.py src/eden/sentinel/scenarios.py tests/sentinel/ docs/hackathon/`
9. `git commit -m "feat(m1): add deterministic solar microgrid simulator"`
10. `git push -u origin feat/m1-microgrid-digital-twin`
11. `gh pr create --draft --base main --head feat/m1-microgrid-digital-twin --title "M1: solar microgrid digital twin" --body "Draft; requires CI, M0 gate review, and owner approval before merge."`

No physical-system controls, real electrical measurements or model API calls are included. Do not merge or advance to M2 until reviewed and explicitly approved.
