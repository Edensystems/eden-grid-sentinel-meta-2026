# M6 Final Verification Matrix

**Verified:** 2026-11-04 · **Branch:** `release/m6-final-submission` · **Base:** `a1aee01` (= `origin/main` at fetch time)
**RC** = release-candidate commit; the exact SHA and CI links are in `M6_RELEASE_STATUS.md`.
Every PASS below was re-executed in this verification. Earlier milestone reports were not taken on trust. Detailed output is in `M6_TEST_RESULTS.md`, and security detail is in `M6_SECURITY_REVIEW.md`.

| Milestone | Requirement | Status | Evidence | Commit | Remaining action |
|---|---|---|---|---|---|
| M0 | FastAPI service starts; `/health` | PASS | `test_health.py`; CI `sentinel-container` health check with `--network none` | RC | — |
| M0 | Typed, strict contracts | PASS | `test_schemas.py`, `test_schema_regressions.py`, `test_validation_regressions.py` | RC | — |
| M0 | CI configured; deps compatible | PASS | `ci.yml`, `m5-preview-ci.yml`, `m6-release-ci.yml`; `pip check` clean on 3.11 and 3.12 | RC | Confirm CI green on RC |
| M0 | No active hard-coded credentials | PASS (tree) / OPEN (legacy refs) | S1–S4 clean; S5 legacy PR refs | RC | Owner: GitHub Support purge, provider revocation proof |
| M0 | Provenance boundary (`src/eden/sentinel/` vs legacy) | PASS | `BASELINE.md`. The M6 changes reuse no legacy EDEN code | RC | — |
| M1 | Solar, essential/flexible loads, battery capacity/SOC, efficiencies | PASS | `test_twin.py`, `test_m1_boundaries.py` | RC | — |
| M1 | Energy conservation | PASS | Max bus residual 0.0 kWh in all 4 scenarios (M6 evidence) | RC | — |
| M1 | Minimum reserve protection | PASS | 0 reserve violations in all scenarios | RC | — |
| M1 | Deterministic, simulation-only | PASS | Byte-identical evidence across 3.11, 3.12 and a repeat run; `mode="simulation"` enforced | RC | — |
| M2 | Meta Model API adapter (OpenAI-compatible, `api.meta.ai/v1`) | PASS | `test_muse.py`, `test_m2_safeguards.py` | RC | — |
| M2 | Strict tool allowlist; validated responses | PASS | `test_m3_tool_is_strictly_allowlisted`; schema plus duplicate-key and size checks | RC | — |
| M2 | Timeouts and bounded retries | PASS | 25 s timeout, SDK retries 0, ≤2 adapter attempts on transient errors only | RC | — |
| M2 | Secure key handling; no automatic paid calls | PASS | Key read from env only. Offline network guard. No live call in CI or M6 | RC | — |
| M2 | Advisory-only authority | PASS | Advisory cannot bypass Guardian or human; scenario-mismatch rejected | RC | — |
| M2 | Live smoke evidence | PASS (limited) | `M2_LIVE_SMOKE_2026-10-31.json`: M1 `cloudy_school_day`, exit 0 | 86bfa54 | M3/M4 live path NOT verified; do not claim it |
| M3 | Forecast generation and error metrics | PASS | Solar MAE reported per scenario | RC | — |
| M3 | Forecast/actual separation (no look-ahead) | PASS | `test_guardian_does_not_depend_on_future_measured_solar`; advisory evidence has no `realized` fields | RC | — |
| M3 | Deterministic constrained scheduling; essential priority; explicit trade-off | PASS | e.g. critical: essential −0.7175 kWh, flexible +0.877 kWh, reported side by side | RC | — |
| M3 | Infeasible scenarios treated honestly | PASS | `degraded` status for 3 scenarios; `night_reserve` shows no change and no claimed gain | RC | — |
| M3 | Local search not claimed optimal | PASS | Method `bounded_pairwise_local_search`; README, runbook and UI say "not a global optimum" | RC | — |
| M4 | Independent Guardian; tampered plan rejected | PASS | `test_m4.py` tamper tests; M6 incident `tampered_plan_denied_by_guardian` | RC | — |
| M4 | Expiry; identity; rejected cannot execute; executes at most once | PASS | `test_m4.py`; M6 incident replay denied | RC | — |
| M4 | Audit chain integrity, including denied actions; plan hash checked | PASS | `test_m4_oversight.py`; M6 verified chains `…rejected,denied` and `…applied,denied` (fixed in R1) | RC | — |
| M4 | Simulation-only actuation; local API disabled by default | PASS | `test_http_api_disabled_by_default`, loopback and token tests | RC | — |
| M4 | In-memory auth not described as production-grade | PASS | README, runbook, security doc and evidence (`volatile_in_memory`) | RC | — |
| M4 | SAM 3.1 | PARTIAL (by design) | Request builder tested offline; **no inference performed or claimed** | RC | Optional; keep unclaimed |
| M5 | Next.js renders; 4 scenarios selectable | PASS | Automated Chrome, desktop and mobile | RC | Owner manual walkthrough |
| M5 | Data from real FastAPI outputs; no fabricated telemetry | PASS | Live API equals in-process simulator; UI values equal API values | RC | — |
| M5 | Baseline vs scheduled trade-off explicit | PASS | Impact panel and progress bars | RC | — |
| M5 | Backend-unavailable state | PASS | Error panel, no numbers rendered | RC | — |
| M5 | Read-only backend; no approval/execution routes | PASS | OpenAPI = 3 GET paths; M4 paths 404, writes 405 | RC | — |
| M5 | Contracts, typecheck, production build | PASS | 10/10, exit 0, exit 0 (Node 26 local) | RC | Node 22 confirmation via CI |
| M5 | Browser console clean | PASS (after R2) | Favicon 404 fixed | RC | — |
| M5 | Local container preview | NOT VERIFIED | Docker absent. Static review only. CI does not build the M5 compose stack | — | Owner: `docker compose -f docker-compose.m5.yml up --build` |
| M5 | Public staging | NOT CLAIMED | Localhost only | — | — |
| M6 | Evidence generator reproducible | PASS | Fingerprint `aa4bbb88…ab5b` | RC | — |
| M6 | Cross-milestone offline incident | PASS | `test_e2e_incident.py` plus M6 incident (the Phase-3 sequence with a fake client; solar is forecast from the prior day, while demand uses the published synthetic load timetable rather than a learned demand forecast) | RC | — |
| M6 | Release CI workflow | PASS (local review) | `m6-release-ci.yml` runs M6 + E2E tests and the generator on 3.11/3.12 and uploads artifacts | RC | Confirm green on RC |
| M6 | README, architecture, security disclosures, submission draft, video storyboard, checklist | PASS (content) | Claims cross-checked against evidence; no overclaims found | RC | Owner fills SHA, video and portal fields |
| M6 | Manual walkthrough, video, eligibility, portal receipt | NOT VERIFIED | Owner-controlled | — | See `M6_RELEASE_STATUS.md` |
