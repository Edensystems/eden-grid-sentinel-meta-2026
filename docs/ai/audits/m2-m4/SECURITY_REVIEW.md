# Security Review — EDEN Grid Sentinel M2–M4

Audit date: 2026-10-31. Secret checks were redacted: commit, variable and value length only. No secret value was displayed or copied. `.env`, `.env.local` and `cred.json` were not opened.

## Critical

### C-1. Non-empty `MODEL_API_KEY` committed at two live branch tips of a public repository
| Commit | Where it is reachable | Value length | Date |
|---|---|---|---|
| `4422e9d` | **current tip of `origin/main`** (and every branch's history) | 48 | 2026-10-30 |
| `c52dbe6` | **current tip of `origin/feat/m1-microgrid-digital-twin` (PR #1)** | 45 | 2026-10-31 19:55 +0300 |

Method: `git show <sha>:.env.example` for every commit, matching `*KEY|TOKEN|SECRET|PASSWORD*` names, reporting empty, placeholder or non-empty plus length. All other commits are empty. The two lengths differ, so these are at least two different values. That suggests a newly issued value was committed again on 2026-10-31, after the first exposure.

Required owner actions (not performed by the auditor):
1. Revoke **both** credentials in the Meta developer dashboard now, and record the revocation date without the key material.
2. Remove the values from branch tips with a normal commit, and get approval before doing it.
3. Decide on history purging (`git filter-repo` / BFG plus force-push). That needs explicit authorization because it rewrites published history. Revocation is the real fix: GitHub forks, caches and clones already have the values.
4. Turn on GitHub secret scanning and push protection, and add a pre-commit secret check.

**Every live M2 verification stays blocked until step 1 is confirmed.**

## High

### H-1. Divergent milestone lineages and a mis-scoped PR
PR #1 is titled "M1: solar microgrid digital twin" but its head `c52dbe6` contains M2, M3 and M4 plus the C-1 credential. PR #2 (M2, `191bbed`) has a different copy of M2 with an extra safeguards test. Merging either as it stands either brings in unreviewed scope or loses the safeguards test, and approving PR #1 would publish C-1 on `main` a second time.

### H-2. Human approves an opaque plan
`ProposalView` gives only `forecast_shifted_kwh` and the Guardian verdict, with no schedule intervals or expected trade-off figures. "Human authorization" is therefore not informed consent to the specific actions. That is acceptable for a synthetic demo, but it must not be described as meaningful oversight.

## Medium

- **M-1. Audit trail gaps.** It is in memory only, so a restart erases it. Truncating the last event is undetectable because there is no external head anchor. The plan content isn't hashed (Guardian re-checks compensate). Failed, denied and race-losing attempts are **not recorded**.
- **M-2. Demonstration-grade M4 auth.** One static bearer token and one env-defined operator. The client-IP check accepts the literal host `testclient`. No TLS, no rate limiting, and the same identity both approves and executes. Default-disabled behaviour is verified (503). This must never be deployed or tunnelled.
- **M-3. Single-process state.** Running `uvicorn --workers N` with N > 1 splits approval state. This is documented but not enforced.
- **M-4. Local M4 commit `64ba350` would silently remove the HTTP gate tests if pushed as is** (5 failing tests). CI would catch it, but that commit has never been through CI.

## Low

- L-1. `AdvisoryResult.model_requests=2` counts logical turns; up to 4 HTTP attempts are possible with retries.
- L-2. Duplicate `functions/scripts/m2_live_smoke.py` in `c52dbe6`, plus root-level `README_M*_PATCH.md` files. This is clutter that should be removed.
- L-3. `/health` still reports `phase: M0`. The container CI check asserts only that value.
- L-4. The working-tree `.env.example` replaces the `PROJECT_ID` placeholder with a real GCP project ID. It isn't a credential, but it should stay out of commits.

## Informational

- I-1. There is no `subprocess`, `os.system`, `eval` or `exec` in `src/eden/sentinel`. The model has no shell, filesystem, cloud or hardware tools. Every endpoint is labelled `simulation`.
- I-2. Inherited Firebase and Pub/Sub code lives in `src/eden/{services,integrations}` and is not imported by `eden.sentinel`.
- I-3. SAM accepts local bytes only, checks magic bytes, caps size at 2 MB and has no URL fetch, so there's no SSRF surface.
- I-4. **Competition eligibility and prior-code rights: NOT VERIFIED.** The repo has no official rules evidence.
- I-5. History scan for other credential shapes (`AIza…`, `sk-…`, long bearer tokens, `"private_key"`) over all commits: the only other hit is `docs/hackathon/M4_RUNBOOK.md`, a false positive (`Read-Host` instructions).
- I-6. No paid Meta API call was made during this audit.
