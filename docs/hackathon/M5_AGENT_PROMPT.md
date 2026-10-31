# Muse Code / Codex engineering handoff — M5

You are the Engineering Orchestrator for EDEN Grid Sentinel. Review `AGENTS.md`, `MILESTONES.md`, `README_M5_PATCH.md`, `M5_RUNBOOK.md`, `M5_REPORT.md` and the prior M2–M4 audit.

Your goal is to integrate the M5 read-only dashboard into a dedicated feature branch without modifying the original EDEN agents, M2 adapter, M3 scheduler or M4 operator approval logic.

1. Record exact branch HEAD, working tree status and currently present files before copying.
2. Apply only this patch to the reviewed feature branch. If files already exist, compare and reconcile instead of overwriting.
3. Verify FastAPI preview exposes *only* GET /health, GET /m3/scenarios, GET /m3/evaluate/{scenario}; fail if M4 or privileged routes appear.
4. Install npm dependencies using an approved registry. Generate and commit package-lock.json, then use npm ci for repeatable CI and Docker builds.
5. Run Python complete suite on 3.11 and 3.12, `npm run test:contracts`, `npm run typecheck`, and `npm run build`. Perform actual browser smoke with all scenarios.
6. Verify empty/offline/malformed response behavior, safe error display, simulation-only labels, no leaked keys, zero hardware calls, no public approval actions, and no fabricated live data.
7. Use Docker Compose only for localhost private demonstration. Do NOT deploy public cloud services or invoke live/billable Meta API.
8. Capture outputs/CI run URLs/commit SHAs in M5_REPORT.md, create a draft PR, and request owner review.
9. Keep unresolved M4.5, credential exposure and official-rule gates explicit. Do not mark them passed based on M5 UI progress.
10. STOP before merge, public staging deployment or M6.
