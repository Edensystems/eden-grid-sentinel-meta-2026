# M6 Security Review — release candidate

**Scope:** tracked tree and staged diff of `release/m6-final-submission`, branch-reachable Git history, the Next.js client bundle, the live M5 preview API, and GitHub-hosted pull refs. No credential values were displayed or recorded during this review. Only match counts and file names were inspected.

## Findings

| # | Check | Result | Evidence |
|---|---|---|---|
| S1 | Hard-coded API keys, tokens, private keys in tracked files | **None found** | `git grep` for `sk-…`, `LLM|…`, `AIza…`, `ghp_/gho_`, `xox?-`, `AKIA…`, `BEGIN … PRIVATE KEY`, `"private_key"`: 0 files. No `MODEL_API_KEY=<value>` assignments. |
| S2 | Tracked `.env` / credential files | **None** | Only `.env.example` and `apps/control-room/.env.example` (placeholders). No tracked `cred*.json`, `*.pem`, `*.key` or service-account files. |
| S3 | Secrets in the staged release diff | **None** | Pattern scan of `git diff --cached`: 0 hits. Rerun immediately before commit. |
| S4 | Branch-reachable history (all local and remote-tracking branches) | **0 key-pattern hits** | `git log --all -p`, consistent with the documented history rewrite. |
| S5 | **Legacy GitHub pull refs** | **OPEN — owner action** | The repository is **PUBLIC**. `refs/pull/1/head` (`c52dbe6…`) and `refs/pull/2/head` (`191bbed…`) are still served by GitHub and contain **3 and 2** key-shaped matches respectively. The history rewrite cannot remove these refs. Only GitHub Support can purge them. |
| S6 | Provider-side key revocation | **NOT VERIFIED** | Owner reported revocation on 2026-10-31. No provider-side confirmation is available to this review. Until confirmed, treat the keys in S5 as potentially live. No attempt was made to use or test them. |
| S7 | Secrets or internal addresses in the frontend bundle | **None** | `.next/static` contains no `SENTINEL_API_BASE_URL`, `127.0.0.1:8000` or `MODEL_API_KEY`. `SENTINEL_API_BASE_URL` is server-only (no `NEXT_PUBLIC_` usage). `lib/upstream.ts` fetches fixed, allowlisted paths only. |
| S8 | Public approval or actuation routes | **None on the M5 preview** | The live API exposes GET `/health`, `/m3/scenarios` and `/m3/evaluate/{scenario}` only. M4 and `/sim/run` paths return 404, and write methods return 405 (see `M6_TEST_RESULTS.md`). |
| S9 | M4 approval API default | **Disabled** | `local_operator` returns 503 unless `M4_ENABLE_LOCAL_API=1`, restricts callers to loopback, and requires a ≥20-character bearer token compared with `hmac.compare_digest`. Covered by `test_http_api_disabled_by_default` and related tests. |
| S10 | Model output authority | **Advisory only** | The M2 adapter permits one allowlisted read-only tool per flow. Unknown tools such as `energize_relay` abort without a second request (`test_m3_tool_is_strictly_allowlisted`). Responses are schema-validated, with duplicate-key rejection and size limits. Advisories attach to proposals only for a matching scenario and never bypass the Guardian or the human decision. |
| S11 | Timeouts and retries | **Bounded** | OpenAI client `timeout=25s`, `max_retries=0`; the adapter makes at most 2 attempts and retries only transient errors (429/5xx, timeout, connection). Exceptions are sanitized. |
| S12 | Network calls in offline tests | **Blocked** | The autouse `tests/conftest.py` guard fails non-loopback connects. 212 tests pass with it active. The M6 generator uses a fake client. No billable Meta request was made during this release verification. |
| S13 | Container exposure (static) | **Loopback-only design** | In `docker-compose.m5.yml`, the UI is published on `127.0.0.1:3000` and the API is on an `internal: true` network with no host port. Runtime NOT VERIFIED (no Docker on host). |
| S14 | Audit and authorization durability | **Demo-grade only (disclosed)** | M4 records are in-memory, single-process, with a static local operator identity. The hash chain detects in-session tampering, and truncation is detected only with a retained head hash. This is not production persistence or authentication, and the README, runbook and submission draft say so. |

## Release-candidate impact

The release candidate **introduces no new security issue**. Its three code changes are an evidence-script hardening, a favicon metadata line and a pytest path setting. S5 and S6 are pre-existing and do not block the technical release-candidate commit. They **do block** representing the project as submission-ready until the owner:

1. Confirms in the Meta provider dashboard that every previously exposed key is revoked (record the date, never the key).
2. Opens or completes a GitHub Support request to purge `refs/pull/1/head`, `refs/pull/2/head` and cached views, and records the ticket ID. Until that is done, do not describe the exposure as removed.

No credential-dependent operation was performed in this review.
