# M4.5 Remediation Report — EDEN Grid Sentinel

**Status: REMEDIATION COMMITTED ON `integration/m2-m4`. OWNER REVIEW REQUIRED. Not merged, not deployed, no billable model call. M5 not started.**

Date: 2026-10-31. Inputs: `docs/ai/audits/m2-m4/` (independent audit, executed evidence).

## Branch

`integration/m2-m4` starts at `c52dbe6` (the pushed M2+M3+M4 tree, 176/176 tests, CI green) and is built non-destructively, with no rebase or force-push:

| Commit | Purpose |
|---|---|
| `8262ccb` | **Merge** of `191bbed` (M2 branch). Restores what the copied M2 lost: `tests/sentinel/test_m2_safeguards.py`, the `meta = ["openai>=2.0,<3"]` extra, and CI installing `.[pipeline,dev,meta]`. `muse.py` / `test_muse.py` were already identical. The `M2_REPORT.md` conflict was resolved in favour of the M2 branch report |
| `fcb7d83` | Blanks the committed `MODEL_API_KEY` in `.env.example` on this branch |
| `bdeba9c` | M2 → M3 read-only tool, advisory-only M2 → M4 attachment, and offline end-to-end incident test |
| (this commit) | Audit documents, this report, and milestone-report addenda |

The local commit `64ba350` (M4 without the router registration) is **not** used. The M4 router is registered because the base `c52dbe6` already registers it.

## Remediation items

| Audit item | Result |
|---|---|
| R1 credential exposure | **Owner reports both exposed keys revoked on 2026-10-31.** That's the owner's statement; it has not been provider-verified by the auditor. Value blanked on this branch tip. History still contains both values (`4422e9d` on `main`, `c52dbe6`), and `origin/main` still carries one at its tip until a fix lands there. Purging requires a separately authorized history rewrite |
| R2 branch topology | Done as above. PR #1 (titled "M1", head `c52dbe6`) and PR #2 (M2) remain open and unchanged; superseding or retitling them is the owner's decision |
| R3 M4 router | Satisfied by the base. OpenAPI includes `/m4/*`; unconfigured requests return 503 |
| R4 M2 integration | `get_m3_evaluation` (enum-limited scenarios, single call, duplicate-key and size limits). Evidence is forecast/MAE plus planned values only, with realized outcomes withheld from the model. `LocalApprovalWorkflow.create(advisory=…)` checks scenario and `requires_human_approval` and stores only headline/risk/model. **The restored M2 safeguard test caught that the first version of this change made the API import `muse`. It was fixed with a type-only import; the safeguard still holds** |
| R5 end-to-end incident | `tests/sentinel/test_e2e_incident.py`: shortfall (1.7175 kWh essential unserved at baseline) → 1.1 kWh shifted plan → fake-client advisory → Guardian denies a tampered plan → rejected proposal can't execute → fresh proposal approved → simulation-only apply → `proposed → approved → applied` chain verifies → realized 1.0 kWh essential unserved (−0.7175 kWh vs baseline), with the flexible trade-off of 0.877 kWh made explicit. Also covers allowlist, forecast-only evidence, and wrong-scenario advisory tests |
| R8 documentation | This report; addenda to the M2/M3/M4 reports; audit documents committed |

## Local evidence (executed)

| Check | Py 3.11.18 | Py 3.12.10 |
|---|---|---|
| `pip check` (`.[pipeline,dev]` + `openai>=2.0,<3`) | no broken requirements | no broken requirements |
| `python -m pytest -q` | **192 passed, 0 skipped** | **192 passed, 0 skipped** |
| Independent probe (66 checks, `D:\apps\_eden_audit\probes`) | M3/M4 results identical to the audit | same |

There are 192 tests: 176 at `c52dbe6`, plus 12 restored M2 safeguards (the `openai`-dependent one now runs), plus 4 end-to-end tests. Container and GitHub Actions evidence comes from the CI run on this branch's pushed SHA, recorded with the owner handoff. Docker isn't installed on the remediation workstation.

## Remaining issues (not fixed here)

1. **Credential history.** Old values remain in published history and on the `origin/main` tip. Revocation is owner-reported only.
2. **Competition eligibility / prior-code rights:** NOT VERIFIED.
3. **Live Muse Spark request:** never run. Fake-client tests prove protocol handling only. Needs explicit billing approval and a fresh key.
4. **M4 oversight gaps (audit R6/R7):** the approver can't see plan intervals; denied and failed attempts aren't audited; tail truncation of the audit chain isn't detected.
5. **In-memory audit (R9):** a restart erases proposals; single worker only; not durable or tamper-proof.
6. **Demo-grade M4 auth:** static token plus loopback; default-disabled; must never be exposed publicly.
7. **Low items:** `/health` still reports `phase: M0`; duplicate `functions/scripts/m2_live_smoke.py`; root `README_M*_PATCH.md` files; 24-interval scheduler horizon; `model_requests` counts logical turns.
8. **Superseded local work:** branch `feat/m4-guardian-human-approval` (`64ba350`) and the uncommitted edits in the primary working tree. That working tree also changes `.env.example` `PROJECT_ID`, which must stay out of commits. Neither was deleted.

## Final gate

Owner review requested for: (a) the `integration/m2-m4` branch and its CI run, (b) what happens to PRs #1 and #2, (c) removing the key from the `origin/main` tip and deciding on history purging, (d) whether R6/R7 must close before M5. No merge, deployment, history rewrite, M5 work or billable call without explicit authorization.
