# EDEN Grid Sentinel — M3 Runbook

**Scope:** deterministic, offline, synthetic forecasting and constrained flexible-load scheduling. No physical device operations, cloud calls, billable Meta requests, or trained AI forecasting model.

## Implemented components

- `m3_forecast.py`: fixed previous-day analogue forecast, and retrospective solar, essential, flexible demand MAE (kW).
- `m3_scheduler.py`: constrained bounded pairwise **local-search heuristic**, not a globally optimal solver. Prioritizes unserved essential demand first, flexible demand second, and minimizes unnecessary retiming.
- `m3_demo.py`: fixed, independent synthetic prior-day profiles and four synthetic school cases, including `critical_priority_school`.
- `m3_routes.py`: simulation-only GET/POST FastAPI endpoints.
- `scripts/m3_demo.py`: offline CLI for reproducible results.

## How the analysis avoids future-information leakage

Planning receives only: (1) independently specified synthetic prior-day solar generation to predict current-day solar, and (2) a **known future school demand timetable**, assumed available before the decision. The scheduler never receives future realized solar values. It uses the M1 simulator on forecast solar to select the schedule. The selected schedule is then replayed on the held-out synthetic realized solar profile. Forecast error is scored **after** the prediction. The response distinguishes `scheduling` (forecast-based planned results) from `realized` (held-out simulator outcomes). Even then, the example is synthetic and cannot establish real-world forecast accuracy.

## Scheduling constraints

For each interval the scheduler may retime aggregate flexible-workload kWh within an inclusive shared window. It must:

- Keep total requested flexible workload energy conserved.
- Keep planned flexible power at or below `flexible_power_cap_kw` within the scheduling window.
- Leave non-shiftable intervals unchanged.
- Keep the M1 battery SOC at or above reserve, and respect charge/discharge power and efficiency.
- Respect M1 essential-first service priority; energy balance residual <= 1e-8 kWh.
- Use a maximum of 24 time intervals, 250 pairwise moves and a strictly bounded quantum.
- Fail closed on invalid window/cap/invalid numeric input.

The heuristic compares `(essential_unserved, flexible_unserved, amount_retimed, curtailment)` lexicographically. It is **not guaranteed to find the global optimum** and has no individual equipment release/deadline rules. `infeasible` is used only when an optimistic total solar+initial battery energy bound proves full service impossible; `not_fully_served` means search did not fully serve loads and is **not** a proof of infeasibility.

The M1 energy accounting and battery bounds remain authoritative. There is no grid import/export, real electrical fault diagnosis, or device control.

## Windows PowerShell

Start with `feat/m1-microgrid-digital-twin` and a new M3 branch. Copy M3 patch contents into the repo, then:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[pipeline,dev]"
python -m pytest -q
python scripts/m3_demo.py --scenario critical_priority_school
python scripts/m3_demo.py --scenario cloudy_school_day --json
python -m uvicorn eden.sentinel.api:app --reload
```

Browse `http://127.0.0.1:8000/docs`:

- `GET /m3/scenarios`
- `GET /m3/evaluate/{name}`
- `POST /m3/evaluate/{name}` with a validated `SchedulingPolicy` body

The API response is simulated, advisory evidence only. Never wire an actuator to these endpoints.

## Review checklist

- Confirm simulator and M2 backward compatibility.
- Run full tests in supported Python 3.11/3.12 and GitHub Actions.
- Verify forecasts and planned scheduling do not read held-out future solar.
- Verify **both** essential and flexible service outcomes on realized solar; improvements are not free savings.
- Verify reserve, energy-balance and power limits, deterministic replay and error-path behavior.
- Confirm source provenance and official Meta hackathon rules before a merge.
- Obtain explicit owner sign-off; do not begin M4 automatically.
