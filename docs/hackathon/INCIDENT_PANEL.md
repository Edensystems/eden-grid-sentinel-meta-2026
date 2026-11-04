# Incident panel — operator mode runbook

The control-room dashboard can run the full incident loop for one local operator:

**Detect → (optional) Meta Muse Spark advisory → Guardian check → human approve/reject → simulated apply → hash-chained audit.**

It is **simulation only** and **loopback only**. Without the operator variables below, the panel shows "Operator mode is off", renders no buttons, and the dashboard stays the read-only M5 preview (this is what `docker-compose.m5.yml` runs).

## Architecture

```text
Browser ──same-origin POST──▶ Next.js route handlers (/api/operator/*)
                               │  server-only bearer token, loopback target only
                               ▼
                    eden.sentinel.api (M4 local API, 127.0.0.1:8001)
                               │  M4_ENABLE_LOCAL_API=1, loopback client check, token check
                               ▼
         LocalApprovalWorkflow ─▶ M3 forecast + scheduler ─▶ Guardian ─▶ in-memory twin + audit
                               │
                               └─ only if requested AND M4_ALLOW_LIVE_ADVISORY=1:
                                  muse.assess_m3_scenario (2 billable requests, advisory only)
```

- The token never reaches the browser: it lives in the Next.js server environment and is sent only to the loopback operator API.
- Writes are refused unless `Origin` equals `Host`, the host is loopback (`127.0.0.1`, `localhost`, `[::1]`; this blocks DNS rebinding) and the body is JSON. Proposal IDs must be UUIDs and scenarios come from an allowlist.
- Every proposal response is re-validated by `lib/incident.ts`. A `mode` other than `simulation`, a broken audit hash link, a stale audit head, or a realized outcome before application is rejected.
- The operator identity is `M4_OPERATOR_ID` on the server. The browser cannot claim a different identity.

## Run it locally (three terminals)

Generate a throwaway token, at least 20 characters. Never reuse a real credential.

```powershell
$env:OP_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
```

```powershell
# 1 — read-only simulation API (charts)
python -m uvicorn eden.sentinel.m5_readonly:app --host 127.0.0.1 --port 8000

# 2 — M4 operator API (loopback only, single worker: state is in memory)
$env:M4_ENABLE_LOCAL_API="1"; $env:M4_OPERATOR_ID="demo-operator"; $env:M4_OPERATOR_TOKEN=$env:OP_TOKEN
python -m uvicorn eden.sentinel.api:app --host 127.0.0.1 --port 8001 --workers 1

# 3 — dashboard in operator mode
cd apps/control-room; npm run build
$env:SENTINEL_API_BASE_URL="http://127.0.0.1:8000"
$env:SENTINEL_OPERATOR_API_BASE_URL="http://127.0.0.1:8001"; $env:SENTINEL_OPERATOR_TOKEN=$env:OP_TOKEN
npx next start -H 127.0.0.1 -p 3000
```

Open http://127.0.0.1:3000/#incident.

### Optional: live Muse Spark advisory (billable)

Only with the owner's billing approval. In terminal 2, before starting the API, also set:

```powershell
$env:M4_ALLOW_LIVE_ADVISORY="1"; $env:MODEL_API_KEY="<from your local secret store; never commit>"
```

The panel's "Ask Meta Muse Spark for a live advisory" checkbox then becomes available. Each proposal opened with it makes **two** Meta Model API requests: one allowlisted read-only tool call, then the final assessment. If the model fails or returns invalid output, **no proposal is created** (fail closed). The advisory is shown as advisory only and cannot approve, execute, or change the plan.

## Demo script

1. **Open incident** on *Critical-load incident*. The forecast shows a 1.889 kWh essential shortfall without action, and the Guardian allows a plan that brings it to 1.000 kWh (forecast) at a flexible-load cost.
2. **Reject plan**, then **Attempt execution**. It is denied, and the audit shows `proposed → rejected → denied`.
3. **Open a fresh proposal**, then **Approve plan** and **Apply to simulation**. On held-out synthetic actuals, essential unserved is 1.000 kWh (−0.718 kWh), and flexible unserved is 0.877 kWh: the trade-off.
4. **Attempt repeat execution**. It is denied, and the audit shows `proposed → approved → applied → denied`.

## Limits (do not overstate)

- In-memory, single-process state with one static local operator identity. This is not production authentication or durable audit.
- Never expose ports 8001 or 3000 in operator mode beyond loopback. The read-only container stack does not enable operator mode.
- With live advisory off, no model output is shown. The panel says so instead of displaying placeholder text.

## Live advisory evidence (2026-11-04)

One owner-approved billable run, recorded in the demo video: *Critical-load incident*, two model requests, one allowlisted M3 tool call. Muse Spark 1.3 returned a **high**-risk advisory ("Degraded synthetic schedule leaves 1.0 kWh essential school load unserved") whose figures match the deterministic plan (1.8885 → 1.0 kWh essential, 1.048 kWh flexible, 1.1 kWh shifted). It stated that nothing was approved or executed. The proposal stayed pending until the operator approved it. Archived as `LIVE_INCIDENT_ADVISORY_2026-11-04.json`. The key was entered by the owner through a hidden prompt, checked against the exposed legacy PR refs, and never displayed.

## Verification (2026-11-04)

- Python: `tests/sentinel/test_m4_operator_panel.py` covers status auth, the advisory gate, fail-closed model errors, missing key, default-policy requirement, advisory-only attachment, and fixture honesty. Full suite: 222 passed.
- Frontend: `npm run test:contracts` 19/19 (incident contract on real M4 fixtures, including tamper cases). Typecheck and build pass.
- Chrome E2E against live servers: reject, then denied execution; fresh proposal, approve, apply, then denied repeat; audit sequences; mobile layout; read-only deployment renders no buttons. Origin probes: cross-site, DNS-rebinding, Origin-less and non-JSON posts → 403.
