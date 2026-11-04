# M6 Demo Checklist

Use this list before recording the video or presenting live. "Verified" items were checked on this release candidate (see `M6_TEST_RESULTS.md`). "Owner" items must be done and observed by a person.

## Setup (verified commands)

```powershell
python -m pip install -e ".[pipeline,dev,meta]"
python scripts/m6_evidence.py --out-dir artifacts/m6     # fingerprint aa4bbb88…ab5b
python -m uvicorn eden.sentinel.m5_readonly:app --host 127.0.0.1 --port 8000
# second terminal
cd apps/control-room; npm ci; npm run build
$env:SENTINEL_API_BASE_URL="http://127.0.0.1:8000"; npx next start -H 127.0.0.1 -p 3000
# or for development: Copy-Item .env.example .env.local; npm run dev
```

## Dashboard

- [x] Verified: all 4 scenarios selectable. Essential shortfall and baseline match the API (automated Chrome, desktop and mobile).
- [x] Verified: energy and SOC charts render. "SIMULATION ONLY" footer present. No approve/execute controls.
- [x] Verified: backend-down state shows an explicit error and renders no numbers.
- [x] Verified: no console errors and no horizontal scroll at 390 px width.
- [ ] **Owner:** manual walkthrough in a real browser window. Confirm the visuals read correctly and record viewport and date.
- [ ] **Owner:** note that the hero copy says "Measured from deterministic simulations". Narrate it as *simulated*, not measured telemetry.

## Incident story (critical_priority_school)

- [x] Verified numbers: essential unmet 1.7175 → 1.0000 kWh (−0.7175), flexible unmet 0 → 0.8770 kWh, 0 reserve violations, final SOC 20%.
- [x] Verified: M4 CLI approve + apply produces `applied`. Reject + apply exits 2. Audit `proposed → approved → applied`.
- [x] Verified offline: fake Muse client → Guardian rejects a tampered plan → human reject → denied execution → fresh approval → single apply → replay denied → full hash chain verified.
- [ ] **Owner:** if showing Muse Spark, use the archived `M2_LIVE_SMOKE_2026-10-31.json` (M1 `cloudy_school_day`, one tool call). Do **not** run a new billable call without approval, and do not claim the M3/M4 path was exercised live.

## Recording hygiene

- [ ] No `.env`, tokens, shell history or provider dashboards visible on screen.
- [ ] Do not show or describe SAM 3.1 inference (request builder only).
- [ ] Do not imply public deployment, hardware control, durable auth or energy savings.
- [ ] Show the CI run URL only after it is green on the final SHA.
- [ ] Check the portal's required video length and format.
