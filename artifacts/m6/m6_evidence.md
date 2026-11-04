# EDEN Grid Sentinel — M6 Offline Verification

**Data classification:** Synthetic simulation; deterministic fake model transport, not a live Meta request.

**Reproducibility fingerprint:** `aa4bbb885ce3ccf912c6dccf174fbccbde21a90c445b69cfc0a627902f83ab5b`

| Scenario | Essential unmet baseline → schedule (kWh) | Flexible unmet baseline → schedule (kWh) | Reserve violations |
|---|---:|---:|---:|
| cloudy_school_day | 2.4000 → 1.5022 | 0.8868 → 1.8000 | 0 |
| critical_priority_school | 1.7175 → 1.0000 | 0.0000 → 0.8770 | 0 |
| night_reserve | 4.0800 → 4.0800 | 2.0000 → 2.0000 | 0 |
| sunny_surplus | 0.0000 → 0.0000 | 0.0000 → 0.0000 | 0 |

## Incident gate checks

- Guardian denied tampered plan: True
- Human rejection enforced: True
- Repeat application denied: True
- Guardian accepted validated plan: True
- In-memory audit chain verified: True

## Limitations

- The output is an **offline synthetic** benchmark, not measured site data or proof of energy savings.
- M2 advice here uses deterministic fake transport, not a live provider request. The separate 2026-10-31 live smoke is documented in the repository.
- M4 audit is in-memory and single-process; it is not a production authorization service.
- This report does not certify cloud staging, official rules eligibility, or the visual browser walkthrough.
