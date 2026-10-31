# Implementation Audit — EDEN Grid Sentinel M2–M4

Audit date: 2026-10-31 · Re-executed with runtime evidence (supersedes the earlier static-only draft of the same date, which contained topology and secret-scan errors — see "Corrections" below).

## Executive summary

The M2, M3 and M4 **code** is real and it works. Every M3 figure in `M3_RESULTS.json` reproduces exactly from the raw synthetic fixtures. Independent physics replay finds no energy-balance, SOC, power-limit or essential-priority violation. The Muse adapter rejects all 9 adversarial model responses tried. The M4 approval state machine holds under replay, expiry, operator-mismatch, forged-ID, post-approval tampering and an 8-thread race.

The **repository state is not releasable**:
1. A non-empty `MODEL_API_KEY` is committed in `.env.example` at the current tip of `origin/main` (`4422e9d`) and at the current tip of PR #1 (`c52dbe6`).
2. M2, "M3" and "M4" are three divergent sibling commits, not a stack, and each is missing pieces the others have.
3. The local M4 commit `64ba350` drops the M4 router and fails 5 tests.
4. M2 is not connected to M3 or M4.
5. Draft PR #1, titled "M1", actually carries M2, M3 and M4.

**Decision: NOT READY FOR M5.**

## Phase A — branch and milestone map (git-verified)

```
4422e9d  origin/main  (CI green; .env.example MODEL_API_KEY NON-EMPTY, len 48)
   └─ c3803cc  M1 simulator
        └─ aa3cf08  M1 docs  ← origin/feat/m3-forecast-scheduler (contains NO M3 code)
             ├─ 191bbed  "implemented M2"   ← origin/feat/m2-muse-spark-integration, PR #2 (open)
             ├─ c52dbe6  "Implemented Milistone 3" ← origin/feat/m1-microgrid-digital-twin, PR #1 (draft "M1")
             │            contains M2+M3+M4; .env.example MODEL_API_KEY NON-EMPTY, len 45
             └─ 64ba350  "Implemented Milistone 4" ← local feat/m4-guardian-human-approval (never pushed)
                          = c52dbe6 minus M4 router registration, minus functions/scripts dup, key blanked
```

Verified facts:
- `191bbed` is **not** an ancestor of `c52dbe6` or `64ba350`. M2 was copied into those commits, not merged.
- Copying lost M2-branch content: `tests/sentinel/test_m2_safeguards.py` (136 lines, 12 tests), the `meta = ["openai>=2.0,<3"]` extra, and CI installing `.[pipeline,dev,meta]`.
- `c52dbe6` and `64ba350` differ only in `api.py` (4 lines: M4 router), `.env.example` (key value), and `functions/scripts/m2_live_smoke.py` (duplicate of `scripts/m2_live_smoke.py`).
- No tags. PR #1 (draft) and PR #2 (open) both target `main`, with divergent copies of `muse.py`.

## Verification matrix

Commit legend: M2 = `191bbed`; M3/M4 pushed = `c52dbe6`; M4 local = `64ba350`. "Probe" means the independent script `D:\apps\_eden_audit\probes\probe_m2_m4.py` (66 checks, see TEST_EVIDENCE.md).

| Milestone | Requirement | Status | Code location | Commit SHA | Test evidence | Gap |
|---|---|---|---|---|---|---|
| M2 | Base URL / model config | PASS | `muse.py` `BASE_URL`, `DEFAULT_MODEL` | all three | `test_muse.py` 28/28 | — |
| M2 | Secure credential config, fail-closed | PASS | `build_meta_client` | all | probe "missing credential fails closed" | — |
| M2 | Tool allowlist and argument validation | PASS | `_tool_spec`, `ToolArguments`, duplicate-key parser | all | probe: unapproved tool, extra argument, scenario swap, malformed JSON all rejected | — |
| M2 | Structured final validation | PASS | `ModelAssessment` strict schema | all | probe: non-JSON, `data_mode=field`, `requires_human_approval=false`, hallucinated kWh field all rejected | — |
| M2 | Timeout, bounded retry, sanitized errors | PASS | `_request` | all | `test_muse.py` retry/sanitize tests | `model_requests=2` counts logical turns, not up to 4 attempts |
| M2 | Model numbers never authoritative | PASS | `Evidence` from `run_simulation` | all | probe: evidence equals local twin summary | — |
| M2 | SDK-level safeguards test | PARTIAL | `test_m2_safeguards.py` | **only `191bbed`** | 11 pass, 1 skipped locally (no `openai`); CI installs `meta` | Lost in `c52dbe6`/`64ba350` |
| M2 | `meta` optional dependency | PARTIAL | `pyproject.toml` | **only `191bbed`** | — | Lost in `c52dbe6`/`64ba350` |
| M2 | Connected to an application flow | FAIL | — | all | probe: `muse.py` imports no M3/M4; nothing imports `muse` | Library and CLI only |
| M2 | Live Muse Spark request | NOT VERIFIED | `scripts/m2_live_smoke.py` | — | not run (no billing authorization; credential exposure unresolved) | Project gate requires it |
| M3 | Deterministic forecast, exact-24h reference, same site | PASS | `m3_forecast.py` | `c52dbe6` | `test_m3.py` 22/22; probe deterministic re-run ×4 | Naive previous-day analogue (labelled honestly) |
| M3 | Reported MAE reproducible | PASS | — | `c52dbe6` | probe: independent MAE equals code equals report for all 4 scenarios (solar/essential/flexible) | — |
| M3 | No forecast leakage | PASS | `m3_demo.evaluate_against_actual` | `c52dbe6` | probe: plan identical under perturbed held-out solar, all 4 scenarios | Future load timetable assumed known (disclosed) |
| M3 | Physical constraints (balance, SOC, power, no simultaneous charge/discharge, essential first, non-negative) | PASS | `twin.py`, `m3_scheduler.py` post-checks | `c52dbe6` | probe: independent replay, max residual 4.4e-16 kWh | — |
| M3 | Flexible energy conservation | PASS | scheduler | `c52dbe6` | probe ×4 | — |
| M3 | Infeasibility explicit; heuristic not oversold | PASS | `status`, method `bounded_pairwise_local_search` | `c52dbe6` | probe: night_reserve full-service gives `infeasible`; >24 intervals rejected | 24-interval horizon vs twin's 336 |
| M3 | Baseline comparison incl. adverse forecast | PASS | `RealizedComparison` | `c52dbe6` | probe: all realized figures match report; optimistic forecast gives −0.0435 kWh essential (worse than baseline) | — |
| M3 | Located on its named branch | FAIL | — | `feat/m3-…` is `aa3cf08` | git | Branch topology |
| M4 | Guardian independently re-derives the plan | PASS | `m4_guardian.py` | `c52dbe6` | probe: post-approval plan edit gives `guardian_rejected_plan` | Rejects any plan not byte-equal to the scheduler's own output |
| M4 | Identified operator, approve/reject, rejected not executable, no re-decision | PASS | `m4_workflow.py` | `c52dbe6` | probe (6 checks) | — |
| M4 | Expiry (15 min) | PASS | `_find` | `c52dbe6` | probe with injected clock; expiry audited | — |
| M4 | Approval bound to operator; replay/concurrency | PASS | `RLock`, `hmac.compare_digest` | `c52dbe6` | probe: 8-thread race gives exactly 1 apply | Single process only |
| M4 | Approver sees what they approve | FAIL | `ProposalView` | `c52dbe6` | probe: view exposes only `forecast_shifted_kwh` and verdict, no intervals | Human approves an opaque plan |
| M4 | Failed/denied attempts auditable | FAIL | `_append` only on success | `c52dbe6` | probe: losing race and mismatched operator leave no event | — |
| M4 | Hash-chain tamper detection | PARTIAL | `verify_audit` | `c52dbe6` | probe: edit detected; **tail truncation undetected**; restart loses all | No external anchor; plan not hashed |
| M4 | HTTP API registered, default-disabled, loopback | PASS at `c52dbe6` / FAIL at `64ba350` | `api.py`, `m4_routes.py` | both | live uvicorn: `c52dbe6` has 10 routes and `/m4` returns 503 unconfigured; `64ba350` has 6 routes and `/m4` returns 404; pytest `64ba350`: 5 failed | — |
| M4 | SAM 3.1 perception | PARTIAL (optional) | `m4_perception.py` | `c52dbe6` | `test_m4.py` builder tests | Request builder only: no inference, masks or visualization |
| X | Phase E end-to-end incident | FAIL at all pushed SHAs | — | — | none exists | M2 link missing |
| X | Reports match code | FAIL | `docs/hackathon/M2–M4_REPORT.md` | all | doc review | Staged Python 3.13 counts, "not pushed", missing secret disclosure |
| X | `/health` phase label | Low | `api.py` | all | live: `"phase":"M0"` | Stale |

## Verdicts

- **M2: PARTIAL.** Offline adapter PASS (runtime-verified). Live connectivity NOT VERIFIED. Not integrated (FAIL). Its safeguards test and `meta` extra survive only on `191bbed`.
- **M3: PASS on functionality, PARTIAL overall.** All numbers reproduce and every constraint holds. It is only PARTIAL because the code isn't on its named branch and arrived through a mis-scoped M1 PR.
- **M4: PARTIAL.** The state machine is strong. It fails three requirements: approver visibility, failed-attempt auditing, and HTTP registration at the local `64ba350`. Audit integrity is partial (in memory only, tail truncation undetected).
- **Cross-milestone: FAIL.** M1 → M3 → M4 works in process. M2 is disconnected and no end-to-end incident exists at any pushed SHA.

## Corrections to the earlier draft of this audit

1. I described the milestones as a linear M1 → M2 → M3 → M4 stack. **Wrong:** they are three siblings of `aa3cf08`.
2. I said the M4 router was missing "at HEAD" and implied everywhere. It is missing **only in the local `64ba350`**; pushed `c52dbe6` registers it and passes 176/176.
3. I said the `meta` extra "was never committed". **Wrong:** it is on `191bbed` and was lost by copying.
4. I said there was "no key in current tracked files". **Wrong:** both `origin/main` and PR #1 tips carry a non-empty `MODEL_API_KEY`. The earlier scan covered only the working tree.
5. The earlier draft had no runtime evidence because shell execution was blocked. This version is fully executed.
