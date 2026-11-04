# M6 Release Status

## Technical status: **TECHNICALLY VERIFIED FOR RELEASE CANDIDATE** — pending CI confirmation on the pushed SHA

All mandatory local technical gates passed on 2026-11-04:

| Gate | Result |
|---|---|
| Full Python suite, 3.11 and 3.12 (`python -m pytest` and bare `pytest`) | 212 passed each |
| Sentinel suite `-v`, 3.11 and 3.12 | 204 passed each |
| Frontend contracts / typecheck / production build | 10/10 · exit 0 · exit 0 |
| M6 evidence generation (3.11 = 3.12 = repeat) | fingerprint `aa4bbb885ce3ccf912c6dccf174fbccbde21a90c445b69cfc0a627902f83ab5b` |
| Cross-milestone offline incident | PASS (`test_e2e_incident.py` plus M6 incident) |
| Live M5 API contract and read-only route check | PASS |
| Automated Chrome walkthrough (desktop, mobile, backend-down) | PASS |
| Security: no new issue introduced; no tracked secrets | PASS (legacy PR-ref exposure open, see below) |

Not verified locally: the M5 Docker Compose stack (Docker not installed) and Node 22 (local Node 26; CI uses 22).

**Release candidate commit:** recorded in the PR and in the follow-up status update once CI completes.

## Competition status: **NOT APPROVED FOR COMPETITION SUBMISSION**

This candidate may **not** be described as approved for submission until the owner completes the following:

| Owner-controlled gate | Status |
|---|---|
| Participant acceptance, team roster and **registered track** (Startup?) confirmed in the portal | NOT VERIFIED |
| Official rules accepted; **pre-existing EDEN code eligibility** confirmed | NOT VERIFIED |
| Provider-side revocation of previously exposed Meta keys confirmed (date only, no key material) | NOT VERIFIED (owner-reported only) |
| GitHub Support purge of public `refs/pull/1/head` and `refs/pull/2/head` (still contain key-shaped strings) | OPEN |
| Manual dashboard walkthrough by a person | NOT DONE |
| Demo video recorded, reviewed and uploaded; real URL | NOT DONE |
| `M6_SUBMISSION_DRAFT.md` links filled (audited SHA, CI, video) and fields matched to the portal | NOT DONE |
| Owner review and merge of the draft PR into `main` | NOT DONE (no automatic merge) |
| Portal submission before **2026-11-04 21:00 ET** and receipt/confirmation ID | NOT DONE |

No merge, deployment, billable model call or competition submission was performed by this verification.
