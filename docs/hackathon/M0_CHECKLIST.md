# M0 checklist and owner gate

- [x] M0-only `/health` API and typed contracts authored under `src/eden/sentinel/`.
- [x] Architecture, risks, demo contract and provenance documented.
- [x] Public GitHub repository URL and initial commit SHA verified and recorded.
- [x] October 27 evidence preserved and distinguished from current verification.
- [x] Validation weaknesses addressed with regression tests.
- [x] Dedicated Sentinel Dockerfile added; inherited EDEN services/image preserved.
- [x] Inherited Firebase/production boundary documented; Python suite blocks external connections.
- [x] Complete Python 3.11 and 3.12 suites pass in the remediation worktree (61 each).
- [x] Current local running HTTP `/health` response verified on both interpreters (HTTP 200).
- [x] Remediation carried into M1 draft PR #1; implementation CI passes both Python jobs and container check (links in `M1_REPORT.md`).
- [ ] Official event rules and pre-existing-code eligibility reviewed with evidence.
- [x] Owner explicitly requested M1 patch application as a draft on 2026-10-30.
- [ ] Formal M0 acceptance, eligibility evidence and approval to merge M1 recorded.

M1 patch application is now explicitly authorized; this does not close the remaining M0 gates. Do not mark eligibility verified or merge M1/start M2 without owner approval.
