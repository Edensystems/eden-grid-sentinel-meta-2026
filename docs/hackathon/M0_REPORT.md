# M0 verification report

This is the preserved M0 verification snapshot. The owner subsequently requested M1
patch application as a draft on 2026-10-30. Current M1 runtime and verification are
recorded in `M1_REPORT.md`; this request does not establish formal M0 acceptance.

Status: **PARTIAL — LOCAL REMEDIATION VERIFIED; GITHUB PUBLICATION BLOCKED**. M1 is not authorized.

## Repository and scope (2026-10-30)

- Repository: https://github.com/Edensystems/eden-grid-sentinel-meta-2026 (public, verified using GitHub metadata).
- Initial/root commit and remote `main` at remediation start: `f3ea5dc1b6f95db98069a7c96003b00bac9c2594`.
- Branch: `m0-remediation`, based directly on that commit in an isolated worktree. Original working copy had local edits to `.env.example` and `tests/sentinel/test_health.py`; neither is included in the remediation commit.
- Current runtime: `src/eden/sentinel/api.py`, launched as `eden.sentinel.api:app`. Only application endpoint is `GET /health`; contracts are in `src/eden/sentinel/schemas.py`, tests in `tests/sentinel/`.
- No Sentinel imports of inherited EDEN runtime modules. Existing EDEN Dockerfile, services, functions, jobs and cloud configuration are preserved. See `BASELINE.md` and `FIREBASE_BOUNDARY.md`.
- No simulator, live model calls, physical controls or cloud deployment implemented.

## October 27 report supplied by the operator

The operator identified this checked-in file as the October 27 verification report. Its recorded evidence was from the **creation environment before the EDEN merge**:

- Python 3.13.5; `python -m pytest -q`: **15 passed in 0.28s**.
- `uvicorn app.main:app --host 127.0.0.1 --port 8765`; `/health` returned HTTP 200 with `{"status":"ok","service":"eden-grid-sentinel","phase":"M0","data_mode":"simulation"}`.
- Package metadata and workflow YAML parsed successfully.

These are retained historical claims, not newly reproduced Python 3.13 results. The old `app/` paths were replaced by `src/eden/sentinel/` at the October 27 merge. The supplied report has no separate workstation or GitHub Actions results filled in.

## Remediation

- Trim free-text strings, reject whitespace-only required fields and non-finite floats.
- Require zero shifted energy for `no_action` and strictly increasing forecast instants, including equivalent instants expressed in different timezones.
- Add regression coverage for creation and assignment validation. Contracts must be revalidated at boundaries; in-place list/nested-object mutation and `model_construct` are not validation APIs. These schemas do not implement a Guardian or authorization.
- Add a dedicated minimal, non-root Sentinel container with health check; copy only Sentinel source and core dependencies. Existing EDEN image is unchanged.
- Block external network connections during Python tests; inherited pipeline I/O stays stubbed. Loopback remains available for Windows asyncio socket pairs.
- Keep Python 3.11/3.12 CI and add an isolated container build/HTTP smoke check.

## Current verification evidence

Verified in the isolated remediation worktree on 2026-10-30 with all `pipeline,dev` extras installed:

| Runtime | Exact test command | Result |
| --- | --- | --- |
| Python 3.11.18 | `.venv311/Scripts/python.exe -m pytest -q` | **61 passed, 1 warning in 4.69s** |
| Python 3.12.10 | `.venv312/Scripts/python.exe -m pytest -q` | **61 passed, 1 warning in 5.08s** |

- Both interpreters: `python -m pip check` reports **No broken requirements found**.
- Both interpreters launched `python -m uvicorn eden.sentinel.api:app --host 127.0.0.1 --port 8765` in turn. A real HTTP GET to `http://127.0.0.1:8765/health` returned **200** and exactly `{"status":"ok","service":"eden-grid-sentinel","phase":"M0","data_mode":"simulation"}`. Both processes were terminated after verification.
- Key installed versions: FastAPI 0.162.0, Pydantic 2.14.2, pytest 9.2.0, httpx 0.28.1. The warning is Starlette's deprecation of its httpx-backed TestClient; no tests failed in the final runs.
- Initial test runs exposed the test network guard blocking Windows asyncio's loopback socket pairs. The guard was corrected, its external-blocking/local-socket behavior tested, and both complete suites rerun successfully.
- Initial dependency installers stalled on network downloads. An IPv4-only pip fallback completed installation; no runtime network behavior was changed.
- Syntax compilation and `git diff --check` pass.

### GitHub publication blocker

The local remediation commit exists on `m0-remediation`. Pushing to origin failed with HTTP 403: local Git authenticates as `bridzer`, which cannot push to this repository. The GitHub connector independently rejected remote branch creation with HTTP 403, **Resource not accessible by integration**. Neither main nor existing Git history was rewritten.

**PR URL: unavailable — no PR was created. CI outcome: unverified — remediation was not published.** Restore repository write access, push `m0-remediation`, open a PR against `main`, and verify both Python matrix jobs and `sentinel-container`. The workflow is authored but is not evidence of a green GitHub run. Existing `main` CI was not verified in this session.

Reproduce from a clean checkout without `.env`, ADC or credentials:

```powershell
python -m pip install -e ".[pipeline,dev]"
python -m pytest -q
python -m uvicorn eden.sentinel.api:app --host 127.0.0.1 --port 8765
# Separate terminal:
Invoke-RestMethod http://127.0.0.1:8765/health
```

Container verification commands are in `FIREBASE_BOUNDARY.md`. No Docker executable is installed on this workstation; container execution must be verified in CI.

## Remaining owner gates

- Official competition rules and pre-existing-code eligibility: **NOT VERIFIED**. No official rules review or owner evidence has been provided.
- Meta credentials/quota: not tested; no live calls authorized or made.
- At the original M0 verification, M1 approval had not been given. The subsequent
  explicit M1 patch request authorizes draft implementation only; merge/M2 remain gated.

M0 remains partial until required evidence and owner review are complete. Current
M1 draft work is explicitly requested; do not merge or advance to M2 without owner approval.
