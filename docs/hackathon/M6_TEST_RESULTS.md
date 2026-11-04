# M6 Test Results — release candidate

**Branch:** `release/m6-final-submission` · **Base:** `main` @ `a1aee01254b10a26ea54f87463a12d51c86ecde9` (equal to `origin/main` at fetch time, 2026-11-04)
**Host:** Windows 11 Pro 10.0.22000 · all commands run from the repository root unless noted. Values below are copied from actual output.

## Runtimes

| Runtime | Version | Source |
|---|---|---|
| Python | 3.11.18 | uv-managed CPython, fresh venv |
| Python | 3.12.10 | python.org CPython, fresh venv |
| Node.js / npm | 26.13.0 / 11.20.0 (local) | CI uses Node 22 (`m5-preview-ci.yml`) |
| Next.js | 16.4.3 (Turbopack) | `package-lock.json` |
| Chrome | system install, driven by `playwright-core@1.52.0` in an isolated temp dir | browser walkthrough only |
| Docker | **not installed** | container run NOT VERIFIED locally |

## Python (each version, separate venv)

```powershell
python -m pip install -e ".[pipeline,dev,meta]"
python -m pip check                      # No broken requirements found. (3.11 and 3.12)
python -m pytest -q                      # 212 passed, 1 warning (3.11 and 3.12)
pytest -q                                # 212 passed, 1 warning (3.11 and 3.12; failed collection before the fix below)
python -m pytest tests/sentinel -v       # 204 passed, 1 warning (3.11 and 3.12)
python -m pytest -q tests/sentinel/test_m6_release.py tests/sentinel/test_e2e_incident.py   # 9 passed (3.11 and 3.12)
```

**Warning (1, both versions):** `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated` raised by the installed FastAPI/Starlette test client. Third-party deprecation; it does not affect assertions. Not suppressed.

The suite installs an autouse guard (`tests/conftest.py`) that fails any non-loopback socket connection, so passing runs show no external network or model calls.

## M6 evidence generator

```powershell
python scripts/m6_evidence.py --out-dir artifacts/m6
# M6 offline evidence validated; scenario_count=4
# meta_step=FAKE_CLIENT_ONLY; M5_api=read_only
# fingerprint=aa4bbb885ce3ccf912c6dccf174fbccbde21a90c445b69cfc0a627902f83ab5b
```

- Byte-identical `m6_evidence.json` from Python 3.11, Python 3.12 and a repeated 3.12 run (`cmp`).
- SHA-256 of files: `m6_evidence.json` `cb1f4db10e772384a7e7c852ac092cab25d1efb7c8bc0770a4b815044492124b`; `m6_evidence.md` `46d0ba076d7983633e867f112d93282b53023d537257ab549bf93f2822c82eab`.
- The staged pre-fix generator was re-run and reproduced the previously staged fingerprint `09a1f1368202b53bff974097974fa4fc3ff2c8373fe8524dc09fbb57cf0887a7` exactly. The fingerprint changed only because the incident evidence gained fields (see remediation R1).

| Scenario | Solar MAE (kW) | Essential unmet baseline → scheduled (kWh) | Flexible unmet baseline → scheduled (kWh) | Shifted (kWh) | Final SOC | Reserve violations | Max bus residual (kWh) | Scheduler status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| cloudy_school_day | 0.2286 | 2.4000 → 1.5022 | 0.8868 → 1.8000 | 1.2 | 0.20 | 0 | 0.0 | degraded |
| critical_priority_school | 0.0500 | 1.7175 → 1.0000 | 0.0000 → 0.8770 | 1.1 | 0.20 | 0 | 0.0 | degraded |
| night_reserve | 0.0000 | 4.0800 → 4.0800 | 2.0000 → 2.0000 | 0.0 | 0.20 | 0 | 0.0 | degraded |
| sunny_surplus | 0.1250 | 0.0000 → 0.0000 | 0.0000 → 0.0000 | 0.0 | 1.00 | 0 | 0.0 | feasible |

`degraded` means full service is not achievable within the constraints. The generator reports this status instead of claiming feasibility.

## Frontend (`apps/control-room`)

```powershell
npm ci --no-audit --no-fund   # added 27 packages, exit 0
npm run test:contracts        # tests 10, pass 10, fail 0
npm run typecheck             # tsc --noEmit, exit 0
npm run build                 # Compiled successfully; 3/3 static pages; routes / , /api/evaluation, /api/health, /api/scenarios; exit 0
```

Run again after the favicon fix (R2), with the same results.

## Backend (M5 read-only API, live process)

`python -m uvicorn eden.sentinel.m5_readonly:app --host 127.0.0.1 --port 8000` (`netstat`: listening on `127.0.0.1:8000` only).

- `GET /health` validates as `PreviewHealth`: `status=ok, phase=M5_PREVIEW, data_mode=simulation, control_mode=read_only`.
- `GET /m3/scenarios` returns the 4 scenarios.
- `GET /m3/evaluate/{scenario}` validates as `M3Evaluation` for all 4 scenarios and equals the in-process `evaluate_fixture()` output exactly.
- An unknown scenario returns 404. `POST /m4/proposals`, `GET /m4/proposals/x`, `POST …/decision`, `POST …/execute-simulation` and `POST /sim/run` return 404. `POST /m3/evaluate/…` and `DELETE /m3/scenarios` return 405.
- OpenAPI paths are exactly `/health`, `/m3/evaluate/{scenario}`, `/m3/scenarios`.

## Browser walkthrough (automated Chrome, production build)

`next start -H 127.0.0.1 -p 3000` was pointed at the live API. A second instance on `:3001` was pointed at a closed port (`127.0.0.1:8999`) to test the real backend-unavailable path.

| Check | Desktop 1440×900 | Mobile 390×844 |
|---|---|---|
| 4 scenario options, each selected in turn | PASS | PASS |
| Rendered essential shortfall and baseline equal the live API values for every scenario | PASS | PASS |
| Energy and SOC charts present (2 SVG charts) | PASS | PASS |
| "SIMULATION ONLY" label present | PASS | PASS |
| No approve/execute controls | PASS | PASS |
| No horizontal overflow | PASS | PASS |
| Browser console errors / page exceptions | none (after R2) | none |

Backend unavailable: error panel "Unable to retrieve authoritative simulation data.", status "API unavailable", **no metrics rendered**, 0 page exceptions. The screenshots were reviewed by eye. They are not committed and are not a substitute for the owner's manual walkthrough.

## M4 CLI

- `python scripts/m4_demo.py --operator demo-operator --decision approved --apply-simulation`: exit 0, status `applied`, audit `proposed → approved → applied`, realized essential unmet 1.0 kWh (reduction 0.7175), flexible unmet 0.877 kWh.
- `--decision rejected --apply-simulation`: exit 2, `error: cannot apply a rejected proposal`.
- Without `--decision`, the CLI prompts for a human decision (EOF in non-interactive shells is expected).

## Container

`docker compose -f docker-compose.m5.yml config/up` was **NOT VERIFIED** because Docker is not installed on this host. A static review found the UI published on `127.0.0.1:3000` only, the API on an `internal: true` network with no host port, read-only root filesystems and a non-root API user. CI's `sentinel-container` job builds and health-checks `Dockerfile.sentinel` (M0 API) with `--network none`. It does **not** build the M5 compose stack.

## Remediation applied during this verification

| ID | Severity | Milestone | Root cause | Fix | Regression |
|---|---|---|---|---|---|
| R1 | Medium (evidence completeness) | M6 | `m6_evidence.py` verified audit snapshots taken *before* the refused execution attempts, so the `denied` events were never part of the verified chain. The incident did not exercise Guardian tamper rejection. | Re-inspect proposals after the refusals, verify the full chains with the retained head hash, require a trailing `denied` event, and add a Guardian tampered-plan step. | `test_incident_enforces_rejection_approval_and_audit` asserts `tampered_plan_denied_by_guardian` and the exact event sequences `proposed,rejected,denied` and `proposed,approved,applied,denied`. |
| R2 | Low (UI) | M5 | `public/favicon.svg` was never referenced, so browsers requested `/favicon.ico` and logged a 404 console error. | `metadata.icons = { icon: '/favicon.svg' }` in `app/layout.tsx`. | Browser walkthrough: console errors none. Contracts, typecheck and build rerun green. |
| R3 | Low (test harness) | M6 | `tests/sentinel/test_m6_release.py` imports `scripts.m6_evidence`, but pytest `pythonpath` held only `src`. Bare `pytest` failed collection, and CI passed only because it uses `python -m pytest`. | `pythonpath = ["src", "."]` in `pyproject.toml`. | Bare `pytest -q`: 212 passed on 3.11 and 3.12. |

No test was weakened, skipped or removed.

## GitHub Actions

On `1bac27a`, all 6 runs succeeded (CI, M5 Preview CI and M6 Submission Evidence CI, on both push and pull_request). CI reports 212 passed on 3.11 and 3.12, the frontend green on Node 22, and fingerprint `aa4bbb88…ab5b` on both Python versions. Run URLs are in `M6_RELEASE_STATUS.md`.
