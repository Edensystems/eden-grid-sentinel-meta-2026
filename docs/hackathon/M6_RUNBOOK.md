# M6 — Reproducible evaluation and final submission runbook

**Competition:** Meta Global AI Developer Hackathon 2026. **Official listing:** https://dev.meta.ai/events/global-hackathon

**Deadline:** 2026-11-04 21:00 EST = 2026-11-05 05:00 EAT. Confirm the time in your accepted-participant portal.

## Ground truth for the demo

The product is a research/demo prototype: one-bus synthetic school microgrid, deterministic battery constraints, naive previous-day forecast, bounded local-search flexible-load scheduler, Meta Muse Spark advisory tool loop, Guardian and manual approval in-memory, and a read-only Next.js operator dashboard.

**Real provider verification on 2026-10-31:** `M2_LIVE_SMOKE_2026-10-31.json` documents a successful single Muse Spark 1.3 tool call + schema-valid advisory on `cloudy_school_day`, after the first token-cap failure. The live M3 tool path has not been verified in that record. The UI does not invoke Muse Spark or expose M4 approvals.

## Step 1 — Clean release verification

On a fresh checkout of main or M6 candidate branch, record HEAD SHA, clean status, Python and Node versions and dependency lockfiles. Do not dump `.env` or secret values.

```powershell
git status --short
git rev-parse HEAD
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[pipeline,dev,meta]"
python -m pytest -q
python scripts/m6_evidence.py --out-dir artifacts/m6
cd apps/control-room
npm ci
npm run test:contracts
npm run typecheck
npm run build
```

Record the exact output and CI URLs in M6_REPORT.md. Neither the Python test count nor Next.js build success may be inferred from old CI.

## Step 2 — Local-only demo and browser evidence

Backend in terminal 1:

```powershell
python -m uvicorn eden.sentinel.m5_readonly:app --host 127.0.0.1 --port 8000
```

Frontend in terminal 2:

```powershell
cd apps/control-room
Copy-Item .env.example .env.local
npm run dev
```

Open http://127.0.0.1:3000 and visibly verify the four scenario choices, charts, trend axes, SOC values, simulation labels, comparison metrics, and fallback/error state. Capture screenshots or a screen recording **only after verifying the actual rendered UI**. Never present the read-only dashboard as a hardware operator UI.

Run M4 CLI simulation separately:

```powershell
python scripts/m4_demo.py --scenario critical_priority_school --operator demo-operator
```

For the offline M2→M3→M4 proof, rely on the repository's `tests/sentinel/test_e2e_incident.py` and the M6 evidence script; fake-client assertions do not count as real Muse access. Approvals are user-supplied and remain in local RAM.

## Step 3 — Evaluations

Read `artifacts/m6/m6_evidence.json` and `m6_evidence.md`. Required disclosure:
- All figures are synthetic; reduction in unmet essential load requires giving up some flexible-load service.
- No economic savings are measured. No physical microgrid was operated.
- Forecast is previous-day analogue, not learned. Optimizer is bounded local search, not a certified global optimum.
- No claim of durable audit/auth; memory and single-worker demo only.
- No claim that SAM 3.1 inference completed: request construction is optional; no masks verified.
- M5 dashboard is read-only with a strict allowlist and does not include live M2 or M4 control.

## Step 4 — Security and eligibility

- Owner reports keys revoked 2026-10-31; verify the provider dashboard and record date without credential material.
- `M45_REMEDIATION_REPORT.md` notes GitHub legacy pull refs and caches requiring GitHub Support cleanup; avoid suggesting those objects are already purged.
- Official rules and treatment of pre-existing EDEN code require owner sign-off. Do not assert compliance from the public event overview alone.
- Confirm submission URL and required fields in the accepted-participant portal. Never invent a valid submission or demo URL.

## Step 5 — Release decision

Only mark M6 **SUBMISSION READY** when the fresh full tests, M6 CI, browser walkthrough, demo video, verified portal requirements, release SHA, key checks, and official rules have evidence. Otherwise mark **CONDITIONALLY READY** or **BLOCKED**, specify remaining items, and submit only claims backed by evidence.
