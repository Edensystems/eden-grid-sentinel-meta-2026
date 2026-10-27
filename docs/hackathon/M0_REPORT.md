# M0 verification report — pending GitHub execution

Status: **PARTIAL — LOCAL STARTER KIT**. Do not advance to M1 yet.

## Inventory
- New files: `app/main.py`, `app/schemas.py`, `tests/`, `pyproject.toml`, `.github/workflows/ci.yml`, `.env.example`, `.gitignore`, docs.
- 2026-10-27: merged into the EDEN repository. `app/main.py` → `src/eden/sentinel/api.py`, `app/schemas.py` → `src/eden/sentinel/schemas.py`, `tests/` → `tests/sentinel/`. See `BASELINE.md`. The validation evidence below predates the merge and used the old paths.
- Runtime: `GET /health` only; no incoming sensor route, AI integration, optimizer, or hardware control.
- Prior EDEN code imported: none.

## Local scaffolding validation (performed in the creation environment)

- Run date: 2026-10-27.
- Python version: 3.13.5 in validation container (target CI matrix: 3.11 and 3.12).
- Command: `python -m pytest -q`.
- Result: **15 passed in 0.28s**.
- Running HTTP check: `uvicorn app.main:app --host 127.0.0.1 --port 8765`, GET `/health` returned **HTTP 200** and `{"status":"ok","service":"eden-grid-sentinel","phase":"M0","data_mode":"simulation"}`.
- Python package metadata and GitHub workflow YAML parsed successfully.
- These results do **not** count as proof of workstation compatibility, GitHub CI, or cloud deployment.

## Developer workstation checks required

```powershell
python --version
python -m pytest -q
python -m uvicorn eden.sentinel.api:app --reload
# Separate terminal:
Invoke-RestMethod http://127.0.0.1:8000/health
```

## To fill after creating remote

- Repository URL:
- Branch / commit SHA:
- `git status --short`:
- Python version:
- Exact local pytest output:
- HTTP health result:
- GitHub Actions workflow run URL / outcome:
- Meta API credentials (state only: configured/not configured; **do not paste key**):
- Rules reviewed (yes/no and source):
- Owner approval (yes/no; date):

## Gate

M0 must remain **PARTIAL** until the repo exists, local verification and CI pass, rules are reviewed, and the owner approves the recorded evidence. Only then write `M0 COMPLETE — AWAITING OWNER APPROVAL` and request explicit approval for M1.
