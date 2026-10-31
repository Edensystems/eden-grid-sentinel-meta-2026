# Integration Matrix — EDEN Grid Sentinel M2–M4

Audit date: 2026-10-31 · Reference SHA: `c52dbe6` (most complete pushed tree; 176/176 tests). Differences at `64ba350` and `191bbed` are noted.

| # | Producer → Consumer | Contract (units) | Code path | Evidence | Status |
|---|---|---|---|---|---|
| 1 | M1 fixtures → M1 twin | `SimulationRequest` (kW, minutes, SOC fraction) → `SimulationResult` (kWh) | `scenarios.py` → `twin.run_simulation` | `test_twin` 24, `test_m1_boundaries` 5; probe physics replay | PASS |
| 2 | M3 prior-day fixture → M3 forecast | Exact −24 h, same site, equal durations | `m3_demo.previous_day_fixture` → `m3_forecast.previous_day_forecast` | `test_m3`; probe MAE ×4 | PASS |
| 3 | M3 forecast → M3 scheduler | Forecast solar replaces actual solar; demand timetable declared known | `m3_demo.evaluate_against_actual` | probe leakage ×4 | PASS (timetable assumption disclosed) |
| 4 | M3 scheduler → M1 twin (oracle and realized) | `SimulationRequest` per candidate; realized = planned flexible profile on held-out actual | `m3_scheduler`, `m3_demo` | probe: realized figures equal report | PASS |
| 5 | M3 → HTTP | `M3Evaluation` JSON, `mode=simulation` | `m3_routes` included in `api.py` | live `GET /m3/evaluate/…` | PASS |
| 6 | M3 → M4 Guardian | `SchedulingResult` + original request + policy; Guardian re-runs the scheduler and compares | `m4_guardian.guard_schedule` | probe: post-approval edit blocked | PASS |
| 7 | M4 Guardian → workflow | `GuardianVerdict` gates create, decide and apply | `m4_workflow` | probe | PASS |
| 8 | M4 workflow → twin (simulated execution) | Approved flexible profile on `target_fixture` actuals | `apply_simulation` | probe: 0.7175 kWh equals M3 report | PASS |
| 9 | M4 workflow → HTTP | `ProposalView`; env-gated, loopback, bearer | `m4_routes` included in `api.py` | live: `c52dbe6` 503 when unconfigured; `64ba350` **404** | PASS at `c52dbe6` / **FAIL at `64ba350`** |
| 10 | M4 → audit | SHA-256 chain over sequence/actor/event/note/time | `_append`, `verify_audit` | probe: edits detected, truncation not; restart loses records | PARTIAL |
| 11 | M4 → human approver | Operator sees `forecast_shifted_kwh` and verdict only | `ProposalView` | probe | **FAIL**: the approver can't inspect the plan |
| 12 | M1 twin → M2 Muse | `Evidence.summary` = local `SimulationSummary` | `muse.assess_scenario` | probe: equals the twin | PASS |
| 13 | M2 Muse → M3 | — | **none** (probe: no `m3_` import in `muse.py`) | — | **FAIL** |
| 14 | M2 Muse → M4 proposal | — | **none** (nothing imports `muse`) | — | **FAIL** |
| 15 | M2 → HTTP | — | none (intentional: no paid-call endpoint) | live OpenAPI | N/A by design |
| 16 | SAM 3.1 → anything | Request dict, `network_call_made=False` | `m4_perception` | `test_m4` | PARTIAL (optional; isolated) |

## Phase E chain

Intended chain: telemetry → M1 → M3 forecast → M3 schedule → **M2 AI** → M4 Guardian → human → twin → audit.

What exists at every pushed SHA is M1 → M3 → M4 Guardian → human → twin → audit, in process. Scenario name is the only correlation key. There is no incident ID spanning stages, and no M2 stage. **No end-to-end incident test exists at any audited SHA.** The uncommitted M4.5 working tree adds one, which has run green locally but hasn't been committed or put through CI.

## Contract consistency

Units are consistent: kW, kWh, SOC fraction in [0, 1], timezone-aware timestamps, `extra="forbid"`, no NaN or infinity. The scheduler's 24-interval horizon is smaller than the twin's 336-interval limit. `schema_version` exists on twin and forecast contracts; M3 and M4 results rely on `Literal` mode and method fields, and there is no version negotiation between stages.
