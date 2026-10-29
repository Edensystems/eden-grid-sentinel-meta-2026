# EDEN Grid Sentinel — M1 Coding Agent Instruction

You are the engineering orchestrator. Work only on M1 (solar microgrid digital twin). Review AGENTS.md, PROJECT_BRIEF.md, MILESTONES.md, docs/hackathon/BASELINE.md, and this M1 patch. The owner explicitly requested M1 patch application on 2026-10-30. M0 is not formally closed; keep official rules and CI confirmation flagged. Local Python 3.11/3.12 verification is recorded in M1_REPORT.md. Do NOT automatically merge or start M2.

1. Continue branch `feat/m1-microgrid-digital-twin`, already created from `main` commit `4422e9d1c16e6c7e4e5903efc5e1861659f4cc08`. The original root commit is `f3ea5dc1b6f95db98069a7c96003b00bac9c2594`. Check `git status` before changes; do not overwrite user changes or recreate history.
2. Apply the contents of the M1 patch to matching repository-relative paths.
3. Verify code remains inside `eden.sentinel` and uses no prior EDEN services, live telemetry, cloud APIs, external model calls, or actuators.
4. Install under Python 3.12 and run the entire test suite. Check the health endpoint, fixture routes, and schema validation.
5. Run all three synthetic fixtures and record exact summary output and energy-balance residuals. Confirm repeatability, reserve, essential priority and charge/discharge constraints.
6. Run static secret scanning on changed files and prove absence of external physical/network I/O in M1 routes.
7. Update M1_REPORT.md with exact test results and CI workflow link; do not invent evidence. Attach the participant rules decision and preexisting-code origin review when available.
8. Commit scoped changes and open a *draft* pull request to `main`. Wait for human review and owner approval before merging or starting M2.

Never rewrite or force-push history. Never expose credentials. Do not close M0 gates without verified evidence.
