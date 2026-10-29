# M1 verification report

**Status: LOCALLY VERIFIED; PUBLICATION PENDING; NOT MERGED OR OWNER-ACCEPTED.**

## Scope and provenance

- Repository: https://github.com/Edensystems/eden-grid-sentinel-meta-2026
- Feature branch: `feat/m1-microgrid-digital-twin`, already based on local and remote `main` at `4422e9d1c16e6c7e4e5903efc5e1861659f4cc08` when this task started. The initial root commit remains `f3ea5dc1b6f95db98069a7c96003b00bac9c2594`. No Git history was rewritten.
- The owner explicitly requested applying this M1 patch on 2026-10-30. That authorizes draft implementation, not formal M0 acceptance, merge or M2.
- The supplied patch files were already present and matched the Downloads copy. Reconciled the patch with M0 remediation `3288389ee67e14dd6aeadac7e915c2a783ba309d`, carrying the actual hardened contracts, offline guard, dedicated Dockerfile and verified documentation into this branch. The worktree gitlink on main had not applied those changes to main's source files.
- New M1 code: `src/eden/sentinel/twin.py` and `scenarios.py`; API adds fixture listing, fixture simulation and bounded custom simulation. `/health` retains its M0 compatibility response. All new runtime code stays in `eden.sentinel`; inherited EDEN services, integrations, agents, Dockerfile and Firebase configuration are unchanged.
- Review fixes: compare interval continuity in UTC (including DST transitions), reuse the hardened Sentinel base schema, and extend storage/power/priority, horizon and repeatability tests.

## Current workstation verification (2026-10-30)

The supported interpreters and full `pipeline,dev` dependencies from the isolated M0 worktree were reused. Pytest's configured `pythonpath=src` selected this feature branch's source. Live checks explicitly set `PYTHONPATH` to this repository's `src`; the loaded API file path was verified to avoid accidentally testing the M0 editable installation.

| Runtime | Exact command from repository root | Result |
| --- | --- | --- |
| Python 3.11.18 | `.remediation-worktree/.venv311/Scripts/python.exe -m pytest -q` | **95 passed, 1 warning in 7.59s** |
| Python 3.12.10 | `.remediation-worktree/.venv312/Scripts/python.exe -m pytest -q` | **95 passed, 1 warning in 7.35s** |

The suite includes inherited pipeline tests with mocked Firebase/Pub/Sub. External socket connections are prohibited; loopback socket pairs remain available for Windows asyncio. The warning is Starlette's deprecation of its httpx-backed TestClient. FastAPI 0.162.0, Pydantic 2.14.2, pytest 9.2.0 and httpx 0.28.1 were installed.

Both interpreters launched `python -m uvicorn eden.sentinel.api:app --host 127.0.0.1 --port 8765` against the feature branch source. Real local HTTP checks returned **200** for `/health`, `/sim/scenarios`, and all three `/sim/scenarios/{name}` routes. OpenAPI contained only `/health`, `/sim/scenarios`, `/sim/scenarios/{name}`, `/sim/run`. Server processes were stopped afterward. POST validation, invalid requests and unknown scenarios are covered by automated tests.

## Synthetic results

Each scenario was run twice; full result JSON was identical and inputs stayed unchanged. Exact summary fields are recorded in `M1_RESULTS.json`.

| Scenario | Solar kWh | Essential unmet kWh | Flexible unmet kWh | Curtailed kWh | Final SOC | Reserve violations | Max abs bus residual kWh |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cloudy_school_day | 7.9 | 2.4 | 0.8868 | 0 | 0.2 | 0 | 1.1102230246251565e-16 |
| night_reserve | 0 | 4.08 | 2 | 0 | 0.2 | 0 | 0 |
| sunny_surplus | 12 | 0 | 0 | 3.8947368421052637 | 1 | 0 | 0 |

Tests independently verify battery storage accounting, bus accounting, reserve, capacity, charge/discharge power limits, essential priority and absence of simultaneous charging/discharging. These are synthetic calculations, not electrical field measurements or validated savings.

## Review and publication evidence

- Static AST review of `api.py`, `twin.py` and `scenarios.py`: imports are limited to datetime/typing, Pydantic/FastAPI and Sentinel modules; no direct file, process, cloud, model or hardware I/O calls were found. Offline guarded tests exercise all simulation routes. This is source/test evidence, not a universal security certification.
- Changed-file secret-pattern scan passed before commit. The populated model-key field inherited in `.env.example` was cleared. A credential-like value remains in earlier Git history; the owner should rotate/revoke it if real. No history rewrite or credential use was performed.
- Remote main SHA was checked. Connector branch creation still returns **HTTP 403 Resource not accessible by integration**. Local Git publication and draft PR outcome will be recorded after the requested attempt.
- Docker is unavailable locally. Container CI is authored, not locally executed.
- GitHub Actions URL/outcome: **pending publication**. PR URL: **pending publication**.

## Earlier archive evidence (not current workstation results)

The supplied patch reported Python 3.13.5, pytest 9.0.2, FastAPI 0.128.2 and Pydantic 2.13.5 with **42 passed in 0.84s** in its creation container. That run omitted inherited pipeline tests and used adapted Sentinel tests. It is historical archive evidence only; current supported-Python full-suite results are above.

## Remaining acceptance gates

- [x] Apply/reconcile M1 patch on the existing feature branch without rewriting history.
- [x] Complete supported Python 3.11/3.12 suites, real HTTP checks and deterministic fixture verification.
- [ ] Publish branch and open draft PR with exact URL.
- [ ] Verify GitHub Actions Python 3.11/3.12 and container jobs.
- [ ] Review official competition rules and pre-existing EDEN eligibility with evidence.
- [ ] Owner accepts M0/M1 evidence and explicitly approves merge.

No Meta calls, measured telemetry, prediction/optimizer functionality, autonomous actions, physical controls or cloud deployment are included. Do not merge or start M2 without explicit owner approval.
