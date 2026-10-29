# M1 — Solar Microgrid Digital Twin

**Scope:** deterministic, synthetic, simulation-only baseline dispatch. No cloud calls, Meta API, forecasts, optimizers, hardware operations, or privileged agent actions.

## Reproducible simulation

Model one off-grid electrical bus with PV generation (kW), essential school demand (kW), flexible demand (kW), and a single battery (capacity in kWh and SOC in [0, 1]). Time intervals are contiguous and timezone-aware. Supply priorities: PV to essential load; PV to flexible load; discharge battery to remaining essential demand; then remaining flexible demand; use excess solar to charge battery, subject to efficiency and charging power/capacity limits. Curtail unused PV. No grid imports/exports.

Charging/discharging efficiencies are fixed constants; battery aging, temperature, reactive power, cables, inverter losses except specified charge/discharge efficiencies, faults, stochastic weather, and voltage stability are not modeled. This is NOT a real electrical simulation and cannot be used to control hardware.

Per interval, energy balance (kWh):

```text
solar_generation + battery_discharge_output
  = essential_load_served + flexible_load_served
    + battery_charge_input + curtailed_solar

battery_stored_end - battery_stored_start
  = battery_charge_input × charge_efficiency
    - battery_discharge_output / discharge_efficiency
```

`energy_balance_residual_kwh` must be within absolute 1e-8, SOC must remain at or above reserve, and charging and discharge cannot both occur in a time interval. No energy optimization or forecast is performed in M1.

## Installation on Windows PowerShell

Use Python 3.11 or 3.12; Python 3.15 is outside project constraints.

```powershell
# From the repo root, after applying the M1 patch and starting a feature branch
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[pipeline,dev]"
python -m pytest -q
python -m uvicorn eden.sentinel.api:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/sim/scenarios
Invoke-RestMethod http://127.0.0.1:8000/sim/scenarios/cloudy_school_day
Invoke-RestMethod http://127.0.0.1:8000/sim/scenarios/night_reserve
```

To submit a custom input, use `http://127.0.0.1:8000/docs` and the `POST /sim/run` endpoint. All requests must validate against `SimulationRequest` and are capped at 336 intervals.

## Three fixed demonstration scenarios

- `cloudy_school_day`: PV declines after mid-day; inspect unmet essential and flexible energy.
- `night_reserve`: no PV and insufficient battery energy; inspect prioritized shortage and reserve protection.
- `sunny_surplus`: excess PV; inspect charging and curtailment.

All are explicitly synthetic, with fixed timestamps and values. Same input must produce the same JSON result. Exact verified summaries are stored in `M1_RESULTS.json`. Interval continuity uses elapsed UTC time, including daylight-saving transitions.

## M1 gate

1. The complete Python suite passes under Python 3.11 and 3.12 GitHub Actions. Local verification currently records 95 passing tests per interpreter; see `M1_REPORT.md` for CI status.
2. Run the sample scenarios twice and compare exact output.
3. Verify summary energy residual, SOC reserve, no simultaneous charge/discharge and priority.
4. No real-asset controls, data writes, background jobs or external model calls appear in the Sentinel routes.
5. Update `docs/hackathon/M1_REPORT.md` with actual operator/CI evidence and branch SHA.
6. Confirm official participant rules and provenance of pre-existing EDEN code before merging.
7. Get explicit owner approval before merging M1 or starting M2.
