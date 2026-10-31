# Test Evidence — EDEN Grid Sentinel M2–M4 Audit

Audit date: 2026-10-31. Everything below was **executed during this audit** unless it is labelled HISTORICAL.

## Environment

| Item | Value |
|---|---|
| OS | Windows 11 Pro 10.0.22000 |
| Interpreters | CPython **3.11.18** (uv) and CPython **3.12.10**, each in a fresh venv under `D:\apps\_eden_audit\` |
| Install | `python -m pip install -e ".[pipeline,dev]"` (same extras as CI on M3/M4 commits) |
| `pip check` | "No broken requirements found." on both |
| pytest | 9.x, `-p no:cacheprovider` |
| Isolation | `git worktree add --detach` per audited SHA under `D:\apps\_eden_audit\wt-<sha>`; operator working tree untouched. `pyproject` `pythonpath=["src"]` confirmed each run imports its own tree (`eden.sentinel.api.__file__` printed per SHA). |
| Not available locally | `docker`, `gh`. Container evidence is taken from CI jobs. CI and PR data come from the public GitHub REST API (unauthenticated GET). |
| Network / billing | No Meta API calls. Muse is exercised with fake clients only. `MODEL_API_KEY` unset during probes. |

## Full-suite results (`python -m pytest -q`)

| Tree | Py 3.11.18 | Py 3.12.10 | Failures |
|---|---|---|---|
| `64ba350` (local M4) | **171 passed, 5 failed** | **171 passed, 5 failed** | `test_health.py::test_m1_routes_are_simulation_only`; `test_m4.py::test_http_api_disabled_by_default`, `::test_http_api_denies_missing_or_wrong_token`, `::test_http_operator_enforced_and_no_double_apply`, `::test_http_auth_does_not_trust_client_claimed_operator`. All are `assert 404 == …` (M4 router not registered) |
| `c52dbe6` (pushed M3/M4, PR #1) | **176 passed** | **176 passed** | — |
| `191bbed` (pushed M2, PR #2) | **134 passed, 1 skipped** | **134 passed, 1 skipped** | skip: `test_m2_safeguards.py:69` "could not import 'openai'" (`meta` extra not installed locally; CI installs it) |
| Working tree = `64ba350` + uncommitted M4.5 edits (not an audit target, reported for the pending decision) | 180 passed | 180 passed | — |

Each run shows 1 warning: Starlette `httpx` TestClient deprecation, informational.

Per-file at `64ba350` (Py 3.12): `test_twin` 24 passed · `test_m1_boundaries` 5 passed · `test_muse` 28 passed · `test_m3` 22 passed · `test_m4` 27 passed / 4 failed · `test_health` 1 passed / 1 failed. 176 tests collected in total.

## Independent probe (`D:\apps\_eden_audit\probes\probe_m2_m4.py <tree>`)

The probe is written outside the repository, runs against `c52dbe6`, and gives identical results on 3.11.18 and 3.12.10. **66 checks: 65 ok, 1 gap confirmed.**
- **M3 (36 checks).** For each of 4 scenarios it recomputes MAE from the raw `HISTORICAL_PROFILES` and target fixtures, checks them against both the code and `M3_RESULTS.json`, and checks every realized and scheduling figure against the report: **all match to 1e-9**. It also runs an independent bus-balance, SOC-recurrence, power-limit, mutual-exclusion, non-negativity and essential-priority replay (max residual 4.4e-16 kWh), flexible energy conservation, a deterministic re-run, and a leakage test (plan unchanged under perturbed actual solar). An adverse forecast produces a −0.0435 kWh essential outcome, worse than baseline. Night reserve under full service gives `infeasible`. Horizons above 24 intervals are rejected.
- **M2 (13 checks, fake client).** Evidence equals the local twin summary. Rejections cover an unapproved tool, an extra argument, a scenario swap, malformed arguments, a missing tool call, non-JSON final output, `data_mode=field`, `requires_human_approval=false`, and a hallucinated extra kWh field. A missing credential fails closed.
- **Cross-module (2 checks).** `muse.py` imports no M3/M4 module, and nothing imports `muse`.
- **M4 (15 checks).** It covers: apply before approval, blank operator, invalid decision, forged ID, rejected proposal can't execute or be re-decided, mismatched operator, an 8-thread concurrent apply (exactly 1 succeeds), audit verification, realized reduction equal to the M3 report (0.7175 kWh), tamper detection, post-approval plan edit blocked, expiry blocks execution and is audited.
- **Limitations confirmed:** tail truncation of the audit verifies (it should not), a restart loses all proposals, and failed/denied attempts are not audited.
- **Gap confirmed:** `ProposalView` gives the approver no schedule intervals.

## Live server (`python -m uvicorn eden.sentinel.api:app --host 127.0.0.1`, Py 3.12)

| SHA | `/health` | OpenAPI paths | `POST /m4/proposals` (env unset) | `GET /m3/evaluate/critical_priority_school` |
|---|---|---|---|---|
| `c52dbe6` | `{"status":"ok",…,"phase":"M0","data_mode":"simulation"}` | 10, including 4 `/m4/*` | **503** (default-disabled ✔) | essential reduction 0.7175 kWh, `mode=simulation` |
| `64ba350` | same | 6, **no `/m4/*`** | **404** | same |

## GitHub Actions (public API, exact SHAs)

| SHA | Branch | Event | Jobs | URL |
|---|---|---|---|---|
| `c52dbe6` | feat/m1-microgrid-digital-twin | push | test (3.11) ✔, test (3.12) ✔, sentinel-container ✔ | https://github.com/Edensystems/eden-grid-sentinel-meta-2026/actions/runs/41222016056 |
| `c52dbe6` | same (PR #1) | pull_request | same ✔ | https://github.com/Edensystems/eden-grid-sentinel-meta-2026/actions/runs/41222022583 |
| `191bbed` | feat/m2-muse-spark-integration (PR #2) | pull_request | test (3.11) ✔, test (3.12) ✔, sentinel-container ✔ | https://github.com/Edensystems/eden-grid-sentinel-meta-2026/actions/runs/41159172010 |
| `aa3cf08` | feat/m3-forecast-scheduler | — | success (M1 code only) | https://github.com/Edensystems/eden-grid-sentinel-meta-2026/actions/runs/41160018439 |
| `64ba350` | — | — | **no runs; never pushed** | — |

CI caveat: the `sentinel-container` job asserts only `/health` with `phase: M0`. It proves that the image builds and boots, not that M2–M4 behave correctly inside the container.

## HISTORICAL claims (not counted as evidence)

The M2, M3 and M4 reports quote 57, 79 and 110 passes from "staged" trees on Python 3.13.5, which is not a supported CI version. None of them matches an audited SHA.

## Reproduce

```powershell
git worktree add --detach D:\apps\_eden_audit\wt-c52dbe6 c52dbe6
cd D:\apps\_eden_audit\wt-c52dbe6; <venv>\python -m pip install -e ".[pipeline,dev]"; <venv>\python -m pytest -q
<venv>\python D:\apps\_eden_audit\probes\probe_m2_m4.py D:\apps\_eden_audit\wt-c52dbe6
```
