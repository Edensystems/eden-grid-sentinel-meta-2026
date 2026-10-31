# M4.5 Remediation Report — EDEN Grid Sentinel

**Status: REMEDIATION COMPLETE ON `integration/m2-m4`, CREDENTIAL HISTORY PURGED. OWNER REVIEW REQUIRED. Not merged, not deployed, no billable model call. M5 not started.**

Date: 2026-10-31. Inputs: `docs/ai/audits/m2-m4/` (independent audit, executed evidence). The audit documents cite pre-purge SHAs; use the map below.

## History purge (owner-approved, 2026-10-31)

Two non-empty `MODEL_API_KEY` values (45 and 48 characters) were committed in `.env.example` in three commits. The owner reports both keys revoked on 2026-10-31 (owner statement, not provider-verified).

Method:
1. A fresh `--mirror` clone in a scratch directory; the developer checkout was not touched.
2. `git filter-repo --replace-text` with the two literal values replaced by an empty string. The value file was deleted immediately after use and the values were never printed.
3. A lease-protected force-push of all five branches, each pinned to its recorded pre-rewrite SHA.

Verification (from a fresh clone of GitHub after the push):
- `MODEL_API_KEY` is empty at every branch tip.
- **0** commits reachable from any branch contain a non-empty value.
- In `main` and `feat/m1`, the only diff from before the rewrite is the `MODEL_API_KEY` line.
- `integration/m2-m4`, `feat/m2` and `feat/m3` have **byte-identical trees** to before, so no code changed.

Pre-purge → post-purge commit map:

| Old | New | Commit |
|---|---|---|
| `4422e9d` | `ccc68b4` | main: Close the engineering deficiencies |
| `c3803cc` | `bde08f7` | M1 simulator |
| `aa3cf08` | `9f4c97e` | M1 docs (`feat/m3-forecast-scheduler`) |
| `191bbed` | `a01d729` | M2 (`feat/m2-muse-spark-integration`) |
| `c52dbe6` | `7fb25f4` | M2+M3+M4 (`feat/m1-microgrid-digital-twin`) |
| `8262ccb` | `1e0ac3b` | merge of M2 into the M2–M4 line |
| `fcb7d83` | — | "blank MODEL_API_KEY": **pruned**, empty after the purge |
| `bdeba9c` | `084f1de` | M2→M3→M4 advisory flow and end-to-end incident test |
| `7708bc1` | `22213b7` | audit documents and first version of this report |
| `8f34bdb` | `7c82371` | M4 oversight fixes |

**What the purge cannot reach:**
- GitHub retains the old commits behind `refs/pull/1/head` and `refs/pull/2/head` (PRs #1 and #2, now closed). Only GitHub Support can remove those, along with cached views.
- Forks and existing clones also keep the old history.
- Every local checkout made before the purge still holds the old objects and must be re-cloned or reset.

## Branch `integration/m2-m4`

It was built from the M2+M3+M4 tree with no rebase. M2 was **merged**, not copied, which restored `test_m2_safeguards.py`, the `meta = ["openai>=2.0,<3"]` extra and CI installing `.[pipeline,dev,meta]`. The local commit `64ba350` (M4 without the router registration) was not used.

## Remediation items

| Audit item | Result |
|---|---|
| R1 credential exposure | Owner-reported revocation; values purged from all branches. GitHub pull refs remain (see above) |
| R2 branch topology | Merge-based integration branch. PRs #1 (mis-scoped "M1") and #2 closed as superseded, with explanatory comments; replaced by one PR from `integration/m2-m4` |
| R3 M4 router | Registered (inherited from the M2–M4 tree); unconfigured `/m4` requests return 503 |
| R4 M2 integration | Allowlisted read-only `get_m3_evaluation`; evidence is forecast-time only. Advisory attachment on M4 proposals has no authority. The restored M2 safeguard caught an API→adapter import in the first draft, which was fixed with a type-only import |
| R5 end-to-end incident | `test_e2e_incident.py`: shortfall → baseline → plan → fake-client advisory → Guardian denial → rejection → fresh approval → simulation-only apply → audit verification → realized vs baseline (−0.7175 kWh essential, 0.877 kWh flexible trade-off explicit) |
| **R6 informed approval** | `ProposalView` now shows the exact Guardian-checked plan per interval (forecast solar, essential demand, original and planned flexible kW) plus forecast essential/flexible unserved before and after |
| **R7 audit gaps** | Every refused decide/apply on an existing proposal adds a hash-chained `denied` event (actor plus reason), including concurrent losers (7 of 8 in the race test), operator mismatch and post-expiry attempts. The `proposed` event records `plan_sha256` over plan, forecast input and policy, re-checked after the Guardian at decide and apply. It catches a coherent edit of all three, which the Guardian alone accepts (regression-tested). `verify_audit(..., expected_head=...)` detects tail truncation |
| R8 documentation | This report; milestone-report addenda; audit documents |

## Evidence

| Check | Result |
|---|---|
| Local full suite, Py 3.11.18 / 3.12.10 (`.[pipeline,dev]` + `openai>=2.0,<3`) | **197 passed, 0 skipped** on both |
| `pip check` | no broken requirements on both |
| Independent 66-check probe | M3 and M4 figures unchanged from the audit. The expected flips are M2 now connected, the gaps "denied attempts unaudited" and "approver can't see plan" now closed, and expiry now followed by the `denied` event |
| GitHub Actions on the final SHA (3.11, 3.12, container) | Recorded on the PR for this branch |

## Remaining issues

1. **GitHub pull refs / caches** still hold the old commits. File a GitHub Support request to purge `refs/pull/1/head`, `refs/pull/2/head` and cached views.
2. **Competition eligibility / prior-code rights:** NOT VERIFIED.
3. **Live Muse Spark request:** **PASS** on the second owner-approved run (`86bfa54`, PR #4), after the first run exposed a too-small final token ceiling. See `M2_REPORT.md` and `M2_LIVE_SMOKE_2026-10-31.json`. The live M3 tool path is not yet exercised.
4. **In-memory audit:** a restart loses proposals; single worker only; not durable. Truncation is detectable only if the caller retains `audit_head_hash`.
5. **Demo-grade M4 auth:** static token plus loopback; default-disabled; must never be exposed publicly.
6. **Low items:** `/health` reports `phase: M0`; duplicate `functions/scripts/m2_live_smoke.py`; root `README_M*_PATCH.md` files; 24-interval scheduler horizon; `model_requests` counts logical turns.
7. **Stale local state:** the developer checkout's local branches (including the never-pushed `feat/m4-guardian-human-approval` at `64ba350`) and its uncommitted edits predate the purge and contain the old history locally. Its `.env.example` changes `PROJECT_ID`, which must not be committed.

## Final gate

Owner review of the PR from `integration/m2-m4` to `main`. No merge, deployment, M5 work or billable call without explicit authorization.
