# M5 implementation report — read-only control room

Date: 2026-10-31.

Status: **READ-ONLY M5 PREVIEW IMPLEMENTED AND VERIFIED LOCALLY ON `feat/m5-readonly-control-room` (DRAFT PR). NOT DEPLOYED, NOT OWNER-ACCEPTED.**

## Base

The patch was authored against the pre-integration branch `feat/m1-microgrid-digital-twin` @ `c52dbe6`. That history was rewritten in the credential purge, and the work was superseded by PR #3/#4. It is applied instead on a feature branch from **`main` @ `7f8f37d`** (M2–M4 integrated, M4.5 remediation merged, live Muse Spark smoke passed). No patch file replaced an existing file, and no M2/M3/M4 business logic was changed.

## Work completed

- **Next.js dashboard** (`apps/control-room`, App Router, TypeScript). Server-side read-only pull of M3 scenario comparisons. It shows connection and error states, interval trend charts, baseline vs scheduled essential/flexible results, explicit trade-offs, scheduling moves and simulation-only labels. The M4 approval interface is explicitly shown as not connected.
- **Fixed route handlers** `/api/health`, `/api/scenarios` and `/api/evaluation`: allowlisted scenarios, 7 s backend timeout, no-store responses, server-only backend address, strict response validation, no generic proxying.
- **M5 FastAPI preview** (`eden.sentinel.m5_readonly:app`): exactly three GET routes, no M2/M4 imports, no writes, no actuation.
- **Docker Compose** blueprint (localhost-only), backend and frontend Dockerfiles, and a CI workflow (Python 3.11/3.12 plus frontend contracts, typecheck and build).

## Changes made during integration

| Change | Reason |
|---|---|
| `package-lock.json` generated and committed; CI and Dockerfile switched to `npm ci` | Reproducible builds, as the patch required. Lockfile v3: 60 entries, all from `registry.npmjs.org`, all with integrity hashes; `npm install` reported 0 vulnerabilities |
| `tests/contract-built/` added to `.gitignore` | Contract-test compile output would otherwise be committed |
| UI service in `docker-compose.m5.yml` also joins a non-internal bridge network | Docker does not publish ports for a container attached only to an `internal: true` network, so `127.0.0.1:3000` would be unreachable. The API stays internal-only, with no host port. **Not executed: Docker is not installed on the verification workstation** |
| New test `test_frontend_contract_fixture_matches_live_backend` | The frontend's "real M3 output" fixture is now checked against the live backend: structure, strings and ints exact; floats to 1e-9 |
| `tsconfig.json` `include` gains `.next/dev/types/**/*.ts` | Added automatically by `next build` 16.4; committed so builds don't rewrite the file |

**Finding while testing:** on Python 3.11, 13 fixture floats differ from 3.12 by at most 8.9e-16 kWh. Python 3.12's `sum()` uses compensated summation (`sum([0.1]*10)` is `0.9999999999999999` on 3.11 and `1.0` on 3.12). This is last-bit noise, not a model difference; a deliberate 0.001 kWh change is still detected.

## Evidence (executed 2026-10-31 on this branch)

| Check | Result |
|---|---|
| Full Python suite, CPython 3.11.18 / 3.12.10 | **207 passed** on both |
| `scripts/m5_contract_summary.py` | PASS: cloudy essential +0.8978 / flexible −0.9132 kWh; critical +0.7175 / −0.8770 kWh; night and sunny 0 / 0; no reserve violations |
| Frontend (Node 26.13, npm 11.20; next 16.4.3, react 19.3.1, typescript 5.9.3) | `test:contracts` **10/10 pass**; `tsc --noEmit` passes; `next build` succeeds; `npm ci` reproduces the install |
| Live HTTP run: uvicorn `m5_readonly` on 127.0.0.1:8000 plus `next start` on 127.0.0.1:3000 | Backend OpenAPI has exactly 3 GET paths; `POST /m4/proposals` returns 404. UI `/api/health` reports `read_only`. All 4 scenarios match `M3_RESULTS.json` (cloudy essential 2.4 → 1.5022 kWh, critical 1.7175 → 1.0 kWh with a 0.877 kWh flexible trade-off) |
| Hostile input | `?scenario=../../m4/proposals`, URL injection, empty or missing scenario all return **400**; POST returns **405** |
| Failure handling | Backend stopped: UI routes return **503** "unavailable", with no fabricated data. Wrong backend (full API with `/m4`): UI **refuses** it (503) because it doesn't declare `control_mode=read_only` |
| Page | 200 with `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options: DENY`, `Permissions-Policy`; no `X-Powered-By`; simulation-only labels rendered |
| Client bundle scan (`.next/static`) | No `NEXT_PUBLIC`, `MODEL_API`, `SENTINEL_API_BASE_URL`, backend address, `api.meta.ai` or `firebase` strings |
| GitHub Actions on the PR head | Recorded on the draft PR |

## Not verified

- **Visual browser walkthrough.** The dashboard renders client-side; the checks above cover the server shell and every API route, but not pixel rendering or interaction. An owner check at `http://127.0.0.1:3000` is required before acceptance.
- **Docker Compose** run (Docker not installed locally); only the CI `sentinel-container` job builds a container image.

## Explicit exclusions

M2 model calls in the UI, the M4 approval UI, public authentication, persistent audit, SAM imagery, cloud deployment, real sensor data, cost-saving claims, and a live M2→M3→M4 incident flow in the UI.

## Remaining gates

- Official competition rules and pre-existing-code eligibility: NOT VERIFIED.
- GitHub Support purge of `refs/pull/1|2/head` (old credential commits).
- Owner browser walkthrough and M5 acceptance; explicit approval before any non-localhost exposure.

**Decision: ready for owner review as a localhost-only read-only preview. Not approved for public staging. Do not start M6.**
