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

## Still to record

- GitHub repo URL: **TO BE RECORDED**.
- Git baseline branch and SHA: **TO BE RECORDED AFTER INITIAL COMMIT** (the EDEN repo had no commits at merge time).
- Meta acceptance: participant states accepted; external confirmation not independently checked.
- Official rules, rights for pre-existing material (now in the same repository) and model/API quota:
  **USER TO VERIFY IN PARTICIPANT PORTAL**.

Never assume the prior EDEN deployment is operational solely from historical logs.
