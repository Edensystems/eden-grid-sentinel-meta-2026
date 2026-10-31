# Milestone M3 — Verification report

**Status: LOCALLY TESTED STAGED PATCH — NOT PUBLISHED, NOT MERGED, NOT OWNER-ACCEPTED.**

## Starting repository evidence, checked 2026-10-31

- Repository: https://github.com/Edensystems/eden-grid-sentinel-meta-2026
- `main`: `4422e9d1c16e6c7e4e5903efc5e1861659f4cc08`.
- M1 `feat/m1-microgrid-digital-twin`: `aa3cf08ffc22471f3407d99f300dcaf70f5ddd64`.
- Draft PR #1 open/unmerged: https://github.com/Edensystems/eden-grid-sentinel-meta-2026/pull/1
- GitHub M1 CI successful for SHA `aa3cf08`.
- No M2 or M3 branch/PR was present in accessible GitHub data at inspection time.
- Remote GitHub connector previously returned 403 `Resource not accessible by integration` for branch creation. This M3 patch is **not pushed**.

## What was built

- Synthetic previous-day analogue forecast with retrospective solar, essential and flexible load MAE; independent hard-coded synthetic prior-day profiles.
- Forecast-based bounded pairwise local search that reschedules aggregate flexible workload without altering total requested kWh, violating power cap/window or bypassing the M1 simulator. Plans use predicted solar and a declared school load timetable; the selected schedule is replayed on held-out actual synthetic solar for realized evaluation.
- Essential-load-first lexicographic objective with explicit sacrificed flexible service if needed.
- Proof-based optimistic supply bound for full-service infeasibility (when requested). Lack of completion by local search is *not* labeled a proof of infeasibility.
- Four deterministic synthetic scenarios, simulation-only API router and CLI.
- Regression tests for forecast input separation, reproducibility, energy balance, SOC, charge/discharge limits, unserved load, invalid policies and HTTP behavior.

## Local evidence in supplied M1+M2 validation environment

- Python 3.13.5 test container: `PYTHONPATH=src python -m pytest -q tests/sentinel` => **79 passed**. This includes M1 source/tests supplied in the archived patch, the M2 archived source/tests and M3 source/tests. This is **not** a full checkout of the current GitHub repository, not a Python 3.11/3.12 CI run and not proof of deployed operation.
- M3-specific tests => **22 passed**.
- Real local uvicorn process: `GET /m3/scenarios` HTTP **200**, `GET /m3/evaluate/critical_priority_school` HTTP **200**. Response reported `mode=simulation`, `status=degraded`, `essential_unserved_scheduled_kwh=1.0`. No model calls, cloud calls or physical controls performed.
- M1 routing and health tests still pass in this staged environment after adding the M3 router.
- Exact measurements and all four synthetic scenarios: see `M3_RESULTS.json`.

## Representative synthetic comparison: critical_priority_school

| Metric | Unchanged baseline | Retimed flexible-load schedule |
|---|---:|---:|
| Unserved essential electricity | 1.7175 kWh | 1.0000 kWh |
| Unserved flexible electricity | 0.0000 kWh | 0.8770 kWh |
| Critical-load deficit reduction | — | 0.7175 kWh |
| Battery reserve violations | 0 | 0 |

**Interpretation:** The previous-day solar projection was used to schedule the known planned loads, and then the resulting schedule was tested on held-out synthetic solar. Earlier flexible demand was retimed, sacrificing some flexible service to protect essential loads later. Tests also show that a worse forecast can reverse the advantage. This is a simulated trade-off, not free energy, a globally optimal plan or real-world savings.

## Model and infrastructure scope

No Meta API calls, trained ML/AI forecasts, external weather information, measured sensor data, optimization solver certification, electrical device control, Firebase write or cloud deployment. Forecasting is a naive reference analogue and scheduling is a bounded local search, not a formally globally optimal mixed-integer program. There is no unit-cost model, real tariff calculation or proof of policy-compliant operational dispatch.

## Unresolved gates

- [ ] Integrate patch into user Git checkout of M1 branch, preserving M2 if locally present.
- [ ] Run full repository tests on Python 3.11 and 3.12 and verify GitHub Actions CI.
- [ ] Manually review endpoints and record exact branch/commit/PR URL.
- [ ] Close outstanding M0/M1/M2 owner and official rules review gates.
- [ ] Rotate any Meta key exposed in earlier public Git history; avoid republishing secrets.
- [ ] Obtain explicit owner sign-off before merging or starting M4.

Do not change this report to `COMPLETE` based on these staged checks alone.
