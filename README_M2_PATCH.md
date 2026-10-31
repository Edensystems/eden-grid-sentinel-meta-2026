# EDEN Grid Sentinel — M2 Muse Spark integration patch

This is a **patch overlay**, not a stand-alone clone. It must be applied on top of the active M1 feature branch of:

https://github.com/Edensystems/eden-grid-sentinel-meta-2026

At preparation, base M1 head: `aa3cf08ffc22471f3407d99f300dcaf70f5ddd64`.

## What's inside

- `src/eden/sentinel/muse.py`: two-turn, tool-using Meta Model API adapter (advisory only).
- `tests/sentinel/test_muse.py`: offline protocol, tool argument, fail-closed and retry tests.
- `scripts/m2_live_smoke.py`: default-off live smoke with two explicit flags.
- `docs/hackathon/M2_RUNBOOK.md`: setup, validation, safety, accepted boundaries and live test.
- `docs/hackathon/M2_REPORT.md`: evidence and remaining gates.
- `docs/hackathon/M2_AGENT_PROMPT.md`: Muse Code / Codex instructions.

## Apply in Windows PowerShell

From the repo root:

```powershell
git fetch origin
git switch feat/m1-microgrid-digital-twin
git pull --ff-only origin feat/m1-microgrid-digital-twin
git switch -c feat/m2-muse-spark-integration
```

Extract ZIP to a temporary directory, then copy its `src/`, `tests/`, `scripts/`, and `docs/` directories into matching repo paths. **Do not copy an outdated M1 version of `api.py`, `twin.py`, or `scenarios.py`; this ZIP does not include them.**

Add the following under `[project.optional-dependencies]` in the existing `pyproject.toml`:

```toml
meta = ["openai>=2.0,<3"]
```

Install and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[pipeline,dev,meta]"
python -m pytest -q
python scripts/m2_live_smoke.py --scenario cloudy_school_day
```

The final command runs **offline**, without contacting Meta.

After reviewing the environment/rotation instructions in `M2_RUNBOOK.md`, a future authorized live smoke can be explicitly run with both `--live` and `--confirm-billing`. No key is included here.

Submit the branch as a **draft PR against the M1 branch** while PR #1 is unmerged. Do not merge until M0/M1 and competition rules have been reviewed.

Suggested commit message: `feat(m2): add bounded Muse Spark advisory tool adapter`.
