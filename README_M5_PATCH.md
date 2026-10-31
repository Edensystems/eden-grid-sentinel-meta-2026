# EDEN Grid Sentinel — M5 Read-Only Control Room Patch

**Assembled October 31, 2026.** Source basis: public `Edensystems/eden-grid-sentinel-meta-2026` feature branch `feat/m1-microgrid-digital-twin` @ `c52dbe67298847f67d5657d91d0cca9d6b65e2d1` (which contains M2–M4 modules, although milestone gates are not yet closed).

> **Integration note (2026-10-31):** the source branch `feat/m1-microgrid-digital-twin` @ `c52dbe6` no longer exists in that form. Its history was rewritten in the credential purge, and its content was merged into `main` through PR #3 (M2–M4 integration and M4.5 remediation). This patch was therefore applied on `feat/m5-readonly-control-room` **branched from `main` @ `7f8f37d`**, and its draft PR targets `main`. The `git` commands below are kept as authored for the record; use the branch above instead. Verification evidence: `docs/hackathon/M5_REPORT.md`.

**Purpose:** Build the M5 visual demonstration now, but do **not** expose the current M4 approval workflow or represent the system as deployed/fully integrated. This is a staged, read-only synthetic preview.

## Apply to existing repository

**First:** preserve local changes. Check `git status` and save/stash only as appropriate. Do not apply to `main`, nor overwrite existing newer files.

```powershell
git fetch origin
git switch feat/m1-microgrid-digital-twin
git pull --ff-only origin feat/m1-microgrid-digital-twin
git switch -c feat/m5-readonly-control-room
```

Extract this ZIP into repository root. It adds only the `apps/control-room/` frontend, `src/eden/sentinel/m5_readonly.py`, `tests/sentinel/test_m5_preview.py`, `scripts/m5_contract_summary.py`, `Dockerfile.m5.api`, `docker-compose.m5.yml`, `.github/workflows/m5-preview-ci.yml`, and M5 documentation. **It does not replace the main `api.py`, import M4 controllers, or modify M2/M3/M4 business logic.**

## Verify backend (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[pipeline,dev]"
python -m pytest -q
python scripts/m5_contract_summary.py
python -m uvicorn eden.sentinel.m5_readonly:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/docs` and `http://127.0.0.1:8000/health`. This preview backend MUST show only `/health`, `/m3/scenarios`, `/m3/evaluate/{scenario}`. It must not register any `/m4` routes. Never run the full M4 API as the staging public backend.

## Verify frontend (second PowerShell terminal)

Requires Node 20.9+; recommended Node 22 and npm. From `apps/control-room`:

```powershell
npm install
npm run test:contracts
npm run typecheck
Copy-Item .env.example .env.local
npm run dev
```

Open `http://127.0.0.1:3000`. Choose any scenario. The UI fetches authoritative synthetic results from the read-only backend and reports actual errors when unavailable. `npm run build` is required before staging acceptance. A lockfile will be generated on first install: **review and commit** `apps/control-room/package-lock.json` for reproducible builds and update Dockerfile/CI to use `npm ci` before release.

## Local-only Docker Compose preview (OPTIONAL)

```powershell
docker compose -f docker-compose.m5.yml up --build
```

The browser UI is bound to `127.0.0.1:3000`; backend is private inside the compose network and exposes **no host ports**. `SENTINEL_API_BASE_URL=http://api:8080` is server-only. Do not change the binding to `0.0.0.0` or deploy this behind public ingress until authentication, credential remediation, and earlier gates have been approved. Docker tests have not been run in this authoring environment.

## Branch publication (after verification)

```powershell
git add apps/control-room src/eden/sentinel/m5_readonly.py tests/sentinel/test_m5_preview.py scripts/m5_contract_summary.py Dockerfile.m5.api docker-compose.m5.yml .github/workflows/m5-preview-ci.yml docs/hackathon/M5_*.md README_M5_PATCH.md
git commit -m "feat(m5): read-only synthetic control room and staging preview"
git push -u origin feat/m5-readonly-control-room
gh pr create --draft --base feat/m1-microgrid-digital-twin --head feat/m5-readonly-control-room
```

This PR is deliberately staged on the currently present feature branch while M0–M4 merge topology is reconciled. Do not merge until an approved integration branch and the M4.5 remediation gate are established. Do not start M6 automatically.
