<p align="center"><img src="apps/control-room/public/eden-logo.png" alt="EDEN logo" width="220"></p>

# EDEN Grid Sentinel

**AI-assisted energy resilience for solar-powered schools** · RavensAI · Meta Global AI Developer Hackathon 2026 · **Push the Frontier**

EDEN Grid Sentinel is a simulation-first prototype exploring how solar-powered schools could prioritize essential loads during solar shortages. It combines a deterministic solar/battery digital twin, a transparent previous-day analogue forecast, bounded flexible-load scheduling, Meta Muse Spark advisory tool-calling, an independent Guardian, local human approval, and a read-only Next.js control-room dashboard.

**Simulation only.** No physical control, field telemetry, verified tariff savings, or production authorization is claimed.

## Quick start (Python 3.11/3.12; Node 22)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[pipeline,dev,meta]"
python -m pytest -q
python scripts/m6_evidence.py --out-dir artifacts/m6
python -m uvicorn eden.sentinel.m5_readonly:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd apps/control-room
npm ci
npm run test:contracts
npm run typecheck
npm run build
Copy-Item .env.example .env.local
npm run dev
```

Open `http://127.0.0.1:3000`. All displayed scenarios and metrics are synthetic and read-only; the UI does **not** connect to the M4 approval demo or make Meta API calls.

## Architecture and constraints

```text
Synthetic M1 grid digital twin
         ↓
M3 historical-analogue forecast → bounded flexible-load scheduling
         ↓
M2 Muse Spark (allowlisted read-only tool; advisory-only reasoning)
         ↓
M4 Guardian (re-check physics, reserve and schedule constraints)
         ↓
Explicit local operator approval or rejection
         ↓
Simulation-only application + in-memory audit

Separately: M5 read-only preview API → Next.js Control Room
```

The forecast and scheduler run on independently supplied synthetic prior-day and target-day fixtures. The schedule is chosen without seeing future solar values and is evaluated afterward on held-out actual synthetic solar. The scheduler is a local search, **not** a globally optimal solver.

## Reproducible result

For synthetic `critical_priority_school`, unmet essential energy changes from **1.7175 kWh to 1.0000 kWh** (a 0.7175 kWh reduction), while unserved flexible demand increases from 0 to **0.8770 kWh**. This illustrates prioritization, not energy creation or validated electricity savings. See `docs/hackathon/M3_RESULTS.json` and the M6 offline evidence artifacts produced with `scripts/m6_evidence.py`.

## Meta AI integration evidence

An authorized live Muse Spark 1.3 smoke test (Oct 31, 2026) validated one M1 scenario: two requests, one approved tool call, structured advisory requiring human approval. Evidence: `docs/hackathon/M2_LIVE_SMOKE_2026-10-31.json`. M3→M4 integration is reproducibly tested with a **fake** model client; the M5 UI does not claim live model access. SAM 3.1 code currently constructs optional segmentation requests only, not validated visual inference.

## Safety, limitations, and provenance

The M4 approval system uses local in-memory state and is not appropriate for public deployment. M5 exposes only GET health and synthetic M3 evaluation routes. No hardware, model credentials, or legacy EDEN Firebase services are needed to run this demo. Previous EDEN infrastructure is present in the repository; see `docs/hackathon/BASELINE.md` and `docs/hackathon/M45_REMEDIATION_REPORT.md` for origin and integration notes. Official hackathon prior-code eligibility must be confirmed with the accepted-participant rules. The owner reports revocation of previously exposed Meta API keys; some old GitHub pull refs/caches may remain accessible pending support cleanup.

## Submission materials

- `docs/hackathon/M6_SUBMISSION_DRAFT.md` — project statement and verified claims.
- `docs/hackathon/M6_RUNBOOK.md` — reproducibility, local demo, and actual evidence capture.
- `docs/hackathon/M6_REPORT.md` — final engineering and release review.

**Project source:** https://github.com/Edensystems/eden-grid-sentinel-meta-2026
