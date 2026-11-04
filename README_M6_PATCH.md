# EDEN Grid Sentinel — M6 Patch Installation

**Repository base checked:** `Edensystems/eden-grid-sentinel-meta-2026` `main` @ `a1aee01254b10a26ea54f87463a12d51c86ecde9` on 2026-11-03.

## Apply safely

1. Save all unrelated local work. In a fresh clone (preferred after the historical credential purge):

   ```powershell
   git clone https://github.com/Edensystems/eden-grid-sentinel-meta-2026.git
   cd eden-grid-sentinel-meta-2026
   git switch -c feat/m6-submission-evidence
   ```

2. Extract this ZIP into the repository root, preserving paths. Do **not** copy `.env` files or credentials. Reconcile `README.md` carefully if the root README changed since the checked base SHA.
3. Install Python 3.11 or 3.12 and execute:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -e ".[pipeline,dev,meta]"
   python -m pytest -q
   python -m pytest -q tests/sentinel/test_m6_release.py tests/sentinel/test_e2e_incident.py
   python scripts/m6_evidence.py --out-dir artifacts/m6
   ```

4. The evidence generator is offline and uses a deterministic **fake Muse client** for M2 protocol testing. It never calls Meta. Compare the recorded live smoke separately: `docs/hackathon/M2_LIVE_SMOKE_2026-10-31.json`.
5. Run the M5 browser walkthrough in the two local terminals described by `M6_RUNBOOK.md`. Do not publish the M4 API, model keys, or physical controls.
6. Fill in factual evidence placeholders in `M6_REPORT.md` and `M6_SUBMISSION_CHECKLIST.md` only after observation.
7. Commit, push and open a reviewable PR from this branch, then inspect the full CI matrix.

   ```powershell
   git add .github/workflows/m6-release-ci.yml scripts/m6_evidence.py tests/sentinel/test_m6_release.py docs/hackathon README.md README_M6_PATCH.md
   git commit -m "chore(m6): reproducible evidence and truthful hackathon submission"
   git push -u origin feat/m6-submission-evidence
   gh pr create --draft --base main --head feat/m6-submission-evidence
   ```

**Never submit fabricated screenshots, unverified cloud URL, or an unreviewed real-world safety claim.**
