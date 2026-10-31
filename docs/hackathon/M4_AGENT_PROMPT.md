# M4 Verification / Integration Prompt for Muse Code

You are the EDEN Grid Sentinel engineering orchestrator working on a hackathon entry. Read `AGENTS.md`, `docs/hackathon/M3_RUNBOOK.md`, `docs/hackathon/M4_RUNBOOK.md`, `docs/hackathon/M4_REPORT.md`, and `docs/hackathon/BASELINE.md`.

## Execute M4 verification only

1. Inspect the current branch, git status, M1/M2/M3 PRs, CI, and provenance. Do not overwrite M2 or M3 edits. First ensure the actual M3 patch is committed on `feat/m3-forecast-scheduler`, since the published branch may be an empty pointer at M1.
2. Create an isolated `feat/m4-guardian-human-approval` branch based on the complete M3 code. Apply the M4 patch. Reconcile `src/eden/sentinel/api.py` and `tests/sentinel/test_health.py` with any other active branch changes.
3. Verify the Guardian recomputes M3 schedules and M1 physics independently, using the forecast-time request only. Do not grant approval based on held-out realized outcomes. Test corrupt schedule and forged metrics denial.
4. Verify explicit identified operator approval or rejection, proposal expiry, replay prevention, in-memory lock, default-disabled API, local operator authentication, audit sequence and mutation detection. Do not call this a production-safe workflow.
5. Verify the SAM request builder is only an optional, offline construction helper. Do not silently call a real model or fabricate segmentation output.
6. Test all existing M1–M3 endpoints, all M4 endpoints in disabled state, supported Python 3.11/3.12 test matrix, and manually test a real local Uvicorn process.
7. Update `docs/hackathon/M4_REPORT.md` with exact test outputs, full commit SHA, CI URLs, app routes, demo outputs, unresolved risks and operator approval status.
8. Stage only intended new/modified files. Scan for secrets before commit. Push a draft PR targeting the exact completed M3 branch. Stop for owner review. Do **not** merge, deploy M4 approval API, call Meta APIs without separate authorization, or implement M5.

**Gate:** M4 remains local implementation pending full CI, earlier eligibility review, owner testing and explicit approval. No electrical equipment may be controlled.
