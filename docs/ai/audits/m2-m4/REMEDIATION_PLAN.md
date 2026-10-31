# Remediation Plan — EDEN Grid Sentinel M2–M4

Audit date: 2026-10-31. **No remediation was performed by this audit.** This plan supersedes the earlier draft, whose items 1, 2 and 4 rested on a wrong topology.

| # | Failure | Root cause | Affected | Severity / consequence | Smallest safe correction | Regression tests | Depends |
|---|---|---|---|---|---|---|---|
| R1 | Live credentials in `.env.example` at the `origin/main` and PR #1 tips | Real values pasted into the template file | `.env.example`; `main`, `feat/m1-…` | **Critical**: billable abuse, key leakage | **Owner** revokes both keys, then a normal commit blanks the tips. Optional history purge only with explicit authorization | Pre-commit/CI secret scan that fails on any non-empty `*_KEY=` in `.env.example` | — |
| R2 | Three divergent milestone commits; M2 safeguards test, `meta` extra and CI `meta` install lost; PR #1 mis-scoped | Copying files instead of merging branches | `191bbed`, `c52dbe6`, `64ba350`, PRs #1 and #2 | High: unreviewable, lossy merges | New branch `integration/m2-m4` from `c52dbe6`, then a **merge** of `191bbed` (keeps both histories and restores `test_m2_safeguards.py`, `meta`, CI). Retitle PR #1 or replace it with a correctly scoped PR. No force-push | Full suite on 3.11/3.12 with `.[pipeline,dev,meta]`; safeguards test not skipped | R1 (so no key is carried forward) |
| R3 | `64ba350` drops the M4 router | Patch applied over an older `api.py` | `api.py` at `64ba350` | High if pushed | **Don't build on `64ba350`.** R2 starts from `c52dbe6`, which already registers the router | Existing `test_health` and `test_m4` HTTP tests | R2 |
| R4 | M2 disconnected from M3 and M4 | M2 scoped to M1 only | `muse.py`, `m4_workflow.py` | High for the demo contract | Allowlisted read-only `get_m3_evaluation` tool (forecast-time evidence only) and an advisory-only attachment on M4 proposals; Guardian and human remain the authority | Fake-client tests: allowlist, wrong scenario, evidence without realized data | R2 |
| R5 | No end-to-end incident test | Milestones tested in isolation | `tests/sentinel/` | High: M5 gate unmet | `test_e2e_incident.py`: shortfall → baseline → plan → AI (fake) → Guardian denial → reject → fresh approve → twin → audit → baseline comparison | The test itself, green on 3.11/3.12 in CI | R4 |
| R6 | Approver can't see the plan | `ProposalView` minimal | `m4_workflow.py` | High (oversight claim) | Add read-only planned intervals plus expected essential/flexible deltas to `ProposalView` | Assert the view contains intervals equal to the Guardian-checked plan | R2 |
| R7 | Failed/denied attempts unaudited; tail truncation undetected | Success-only `_append`; no anchor | `m4_workflow.py` | Medium | Record `denied` events (the event `Literal` needs extending); return the head hash with every view so truncation becomes detectable; hash the plan and policy into the `proposed` event | Race test asserts N−1 denied events; truncation test fails verification | R2 |
| R8 | Reports out of sync | Written against staged trees | `docs/hackathon/M2–M4_REPORT.md`, M4.5 report | Medium | Rewrite against the final SHA and CI URLs; label staged results; disclose C-1 and the R1 status | Docs checklist in PR | R2–R5 |
| R9 | In-memory audit, single worker | Demo scope | `m4_workflow.py` | Medium | Append-only local JSONL/SQLite (simulation only); enforce one worker | Restart-recovery test | Owner scope decision |
| R10 | Minor items | — | `api.py` phase label, duplicate `functions/scripts/`, `README_M*_PATCH.md`, `model_requests` naming | Low | Remove or rename | Update the health test | R2 |

## The uncommitted M4.5 working tree

The working tree (`64ba350` plus uncommitted edits, 180/180 green locally) already contains R4, R5 and a router fix. It also has a fresh `meta` extra that duplicates `191bbed`'s. **It's built on the wrong base:** `64ba350` instead of `c52dbe6` + `191bbed`, and it still lacks `test_m2_safeguards.py` and the CI `meta` install. Its reports (`M45_REMEDIATION_REPORT.md` and the addenda) describe the old, incorrect topology.

Recommendation: **don't commit it as is.** Re-apply only its `muse.py` / `m4_workflow.py` / `test_e2e_incident.py` changes on top of R2's merge branch, drop its `api.py` and `pyproject.toml` hunks (already present after R2), and leave `.env.example` out entirely.

## Order

R1 (owner, now) → R2 → R3 (automatic) → R4 → R5 → R6 → R7 → R8 → push the integration branch, then CI on the exact SHA → re-audit → owner M5 decision. R9 and R10 as scope allows.
