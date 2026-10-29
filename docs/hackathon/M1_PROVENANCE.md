# M1 provenance and status

Repository: https://github.com/Edensystems/eden-grid-sentinel-meta-2026

Original root: `f3ea5dc1b6f95db98069a7c96003b00bac9c2594`. Feature branch `feat/m1-microgrid-digital-twin` was already based on current main `4422e9d1c16e6c7e4e5903efc5e1861659f4cc08` when the owner requested applying the patch on 2026-10-30. It was preserved without rewriting history.

`twin.py`, `scenarios.py`, M1 tests, runbook and synthetic results are hackathon-new development supplied in the patch and reviewed locally. `api.py` extends the M0 scaffold and preserves `/health`. M0 remediation from `3288389ee67e14dd6aeadac7e915c2a783ba309d` is carried forward as source/documentation, rather than relying on the worktree gitlink tracked in main. The twin reuses Sentinel's hardened `StrictSchema`. No M1 module imports inherited `eden.agents`, `eden.integrations`, `eden.services` or `eden.core`. Those inherited implementations and Firebase configuration remain unchanged.

Local supported-Python and HTTP evidence is in `M1_REPORT.md`; exact synthetic summaries are in `M1_RESULTS.json`. GitHub publication/CI require separate evidence. Official participant rules and eligibility for pre-existing code remain unverified. Applying a draft M1 patch does not constitute formal M0 acceptance or authorize merge/M2.
