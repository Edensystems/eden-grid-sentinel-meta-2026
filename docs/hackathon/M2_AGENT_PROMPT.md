# M2 engineering orchestrator prompt

You are the principal engineer for EDEN Grid Sentinel, the Meta Global AI Developer Hackathon 2026 entry.

Current M1 branch: `feat/m1-microgrid-digital-twin`; draft PR #1. Work on M2 in a **separate feature branch from M1**, not from `main` until M1 has merged.

Before editing, read `AGENTS.md`, `docs/hackathon/M1_REPORT.md`, `docs/hackathon/M2_RUNBOOK.md`, the `src/eden/sentinel/` code, and the new M2 tests. Preserve existing EDEN pipelines. No refactor of older agents or live hardware operations.

## M2 tasks

1. Audit the target branch, working tree, and existing M1 runtime; do not overwrite local changes.
2. Integrate M2 overlay files under their matching repo paths, without copying an entire older repo or introducing new secret values.
3. Add a pinned major-version `meta` optional dependency in `pyproject.toml`: `openai>=2.0,<3`.
4. Run the whole offline suite on Python 3.11 and 3.12 with external networking disabled. Verify the adapter sends only `tool_choice="auto"`, enforces tool/JSON validation and bounds token usage.
5. Ensure no public endpoint triggers provider billing. Validate error handling and no leakage of the model key in code or logs.
6. Demonstrate an offline fixture summary. A live call is a separate owner-approved, explicitly billable step; never call Meta just because the key exists in the environment.
7. Document code provenance, exact versions, CI outcomes, remaining risks and M2 status. Open a **draft** PR (preferably targeting M1's branch until M1 merges).
8. Do not merge, deploy, authorize live equipment actions or advance to M3 without owner approval.

## Gate

Deliver a test-backed M2 report with PR URL and all remaining blockers. Stop for owner review.
