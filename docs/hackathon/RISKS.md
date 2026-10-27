# Risk register (current at M0)

| Risk | Severity | Mitigation | Owner / gate |
| --- | --- | --- | --- |
| Hackathon rules limit earlier code or external software | High | Review participant portal and official rules; track every source and license | Founder, before any EDEN import |
| Meta API access or quota unavailable | High | Offline mocked agent adapter in M2; authorize one live integration test | M2 gate |
| Eight-day schedule / scope expansion | High | Prioritize full vertical slice; optional image segmentation last | Every milestone |
| AI produces nonphysical or dangerous recommendation | Critical | Deterministic solver and Guardian validator; no physical controls | M3/M4 |
| Data and simulation presented as real deployment | High | Clear simulated/measured labels; no invented benchmarks | All |
| Credential leakage | Critical | Ignored `.env`, secret scanning, no logs of tokens | All |
| OS/runtime mismatch (Windows vs CI Linux) | Medium | CI Python 3.11 and 3.12; local verification on Windows | M0 |
| Duplicate/out-of-order Pub/Sub events (if later adopted) | Medium | Unique event IDs, idempotency and ordering strategy | Later deployment |
| Physical asset segmentation misread as fault diagnosis | Medium | SAM restricted to equipment inventory; no electrical inference from masks | M4 |
