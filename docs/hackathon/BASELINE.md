# Baseline / provenance record

- Project: EDEN Grid Sentinel, RavensAI entry for the Meta Global AI Developer Hackathon 2026.
- Date initiated: 2026-10-27.
- **2026-10-27 — merged into the EDEN repository.** The Sentinel M0 scaffold was originally a separate greenfield
  directory (`eden-grid-sentinel-meta-2026`, never under Git). At the owner's request it was copied into the
  existing EDEN repository. The source directory was left unchanged.

## Where code comes from

| Path | Origin |
| --- | --- |
| `src/eden/sentinel/` (`api.py`, `schemas.py`) | Hackathon-new (Sentinel M0 scaffold, 2026-10-27) |
| `tests/sentinel/` | Hackathon-new (Sentinel M0 scaffold) |
| `docs/hackathon/ARCHITECTURE.md`, `DEMO_CONTRACT.md`, `RISKS.md`, `M0_CHECKLIST.md`, `M0_REPORT.md` | Hackathon-new (Sentinel M0 scaffold) |
| `.github/workflows/ci.yml` | Hackathon-new, extended to also install and test the EDEN pipeline |
| `src/eden/{core,integrations,agents,services}/`, `functions/`, `jobs/`, `tests/test_pipeline.py` | **Pre-existing EDEN** (Sense/Think/Learn/Act pipeline, Firebase, Pub/Sub), consolidated and refactored on 2026-10-27 |

The Sentinel code does **not** import pre-existing EDEN modules. Any future reuse of `eden.agents`,
`eden.services` or `eden.integrations` from `eden.sentinel` must be recorded here with the commit SHA.

## Verified Git provenance (2026-10-30 remediation)

- Repository: https://github.com/Edensystems/eden-grid-sentinel-meta-2026
- GitHub metadata confirms the repository is **public**, with default branch `main`.
- Initial/root commit and remediation base: `f3ea5dc1b6f95db98069a7c96003b00bac9c2594`
  (`chore: establish EDEN Grid Sentinel M0 baseline`). Local history and remote `main`
  resolve to this SHA at remediation start. It contains both inherited EDEN and the M0
  scaffold; it does not independently establish the creation dates of inherited material.
- Remediation branch: `m0-remediation`, created directly from that `main` commit.
- Existing `Dockerfile`, Firebase configuration, `functions/`, `jobs/`, and all code
  under `src/eden/` outside `sentinel/` remain pre-existing EDEN and are not modified.
- `Dockerfile.sentinel` is hackathon-new packaging, installing only core dependencies
  and copying only `src/eden/sentinel/`. Sentinel does not reuse inherited runtime modules.
- Remediation adds validation regression tests, an external-connection test guard, container CI,
  and documentation; using inherited pipeline tests verifies them with mocked I/O only.

## M1 patch integration (2026-10-30)

- Current local and remote `main` at M1 start: `4422e9d1c16e6c7e4e5903efc5e1861659f4cc08`.
  Feature branch `feat/m1-microgrid-digital-twin` was already based on that commit.
- The supplied Downloads patch was already copied into the working tree. Its M1 modules,
  tests and documentation were verified against the supplied files before editing.
- The M0 remediation at `3288389ee67e14dd6aeadac7e915c2a783ba309d` existed only
  in the separate worktree; main tracked a worktree gitlink, which does not apply those
  source changes. M1 carries the actual M0 schema, documentation, isolation and packaging
  files forward explicitly. The local worktree and inherited source are preserved.
- `twin.py`, `scenarios.py`, M1 tests/runbook/results are hackathon-new.
  The twin reuses Sentinel's M0 `StrictSchema`; no inherited EDEN runtime is reused.
- Official rules and pre-existing-code eligibility remain unverified.

## Owner evidence still required

- Meta acceptance: participant states accepted; external confirmation not independently checked.
- Official rules, rights for pre-existing material (now in the same repository) and model/API quota:
  **USER TO VERIFY IN PARTICIPANT PORTAL**.

Never assume the prior EDEN deployment is operational solely from historical logs.
