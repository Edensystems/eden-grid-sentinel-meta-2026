# Milestone M5 — Control Room and Safe Staging Preview

## Scope

Read-only Next.js dashboard driven by an isolated FastAPI preview application. The backend uses M3 `evaluate_fixture` (a deterministic previous-day analogue forecast, bounded local-search scheduling and held-out synthetic evaluation). No real devices, cloud writes, live model inference, or approval endpoints. M4's simulation-only state machine exists elsewhere but is **not** exposed by this preview application.

## End-to-end data contract

`apps/control-room` browser -> `GET /api/{health,scenarios,evaluation}` (Next server-only route handlers) -> fixed `SENTINEL_API_BASE_URL` (FastAPI M5 preview) -> `GET /{health,m3/scenarios,m3/evaluate/{scenario}}` -> normalized whitelisted fields -> browser visualizations.

The frontend rejects unsanctioned scenario names, invalid modes, nonfinite data, unmatched forecast timestamps, out-of-bounds SOC, positive reserve violations and large bus-energy residuals. Errors produce unavailable UI instead of sample telemetry. The browser never receives a Meta key, Firebase credential, or API control token.

## UI content and limitations

- Solar and load time series are derived from M3 simulation intervals. Units kW; derived as interval kWh divided by interval hours.
- Battery panel compares baseline and scheduled state-of-charge trajectories; metric is final scheduled SOC.
- Baseline/scheduled unmet essential and flexible demand are from **realized** simulation, not predicted outcomes.
- Change in flexible shortfall is explicitly displayed when protection of essential loads imposes a cost.
- Moves table uses M3 scheduling moves; zero moves is a valid condition.
- Forecast MAE uses synthetic retrospective evaluation, not production forecast accuracy.
- No authentication, public operator approval, persistent audit, or genuine agent trace is implemented in the preview.

## Security boundaries

- Backend app `eden.sentinel.m5_readonly:app` is GET-only and does not import M4 routes or M2 model adapters.
- Frontend Next route handlers are fixed and read-only; there is no generic path proxy or POST support.
- Preview frontend and backend must remain localhost/private-tenant only until release/security gates pass. Read-only does not remove the need for authentication if site data changes to measured data.
- No live model calls, real sensor ingestion, or hardware control are permitted.
- The historical Meta API key exposure was remediated on 2026-10-31: the owner reports the keys revoked, and the values were purged from all branches. GitHub still retains the old commits behind closed PRs #1/#2 until a Support request removes them.

## Mandatory testing before completion

1. Full repo Python tests on 3.11 and 3.12 (not just staged patch tests).
2. `tests/sentinel/test_m5_preview.py` and OpenAPI GET-only inspection.
3. Next.js install, TS typecheck, contract tests, production build and local browser walkthrough.
4. Validate browser errors when backend unavailable, malformed, or slow.
5. Verify no `/m4/` routes on the **staging preview** backend.
6. Verify no credentials in frontend bundles and no `NEXT_PUBLIC_` secret references.
7. Docker Compose localhost smoke with no public/host API mapping.
8. Official rules review and owner deployment approval, handled separately (M4.5 remediation was merged in PR #3/#4).

## Acceptance gate

Ready for local M5 preview when all applicable offline tests, builds and browser walkthroughs pass. **NOT ready for external staging deployment** until compliance (competition eligibility) checks and an approved authentication/ingress model are evidenced. M5 does not certify M2–M4 integrated behavior.
