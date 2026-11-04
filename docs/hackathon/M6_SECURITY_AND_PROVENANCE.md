# Security, provenance, and evaluation boundaries

## Trust boundaries

- External Meta model output is advisory only; it cannot invoke a device-control, shell, Firebase or filesystem tool through the M2 allowlist.
- The M3 simulator and scheduler own all physically relevant calculations. Synthetic observation is distinct from prior-day forecast. Model text is not a source of authority for numeric energy evidence.
- M4 Guardian recomputes physics, enforces constraints and requires explicit operator authorization in a **local single-process** demonstration. Hash chaining aids in-session audit verification but is not durable, globally tamper-proof logging.
- The M5 preview is a separate read-only ASGI app. It has no approval routes and does not invoke the provider. The Next.js frontend does not expose backend secrets.

## Known limitations and unresolved owner checks

- Historical Meta keys were present in Git; the owner reported revocation, and a rewritten history removed them from branch-reachable commits. Old pull refs `refs/pull/1/head`, `refs/pull/2/head` and caches may still require GitHub Support cleanup. Verify provider-side revocation independently.
- Official competition rules / prior-code eligibility are not evidenced in GitHub documentation.
- Legacy EDEN services exist in the same repository; Sentinel itself avoids importing older cloud services in its evaluation path. Attribution/provenance are documented in BASELINE.md and M45_REMEDIATION_REPORT.md.
- No durable M4 records, production SSO/RBAC, real sensor authentication, field validation, or distributed locking.
- No actual SAM 3.1 masks or fault detection were demonstrated.
- Staging as configured is localhost-only. Never expose the M4 approval demo route on a public host.

## Evidence categories

**Live Meta inference:** 2026-10-31 one authorized M1 scenario smoke, documented exact result.

**Offline AI integration:** deterministic fake-client in test suite and M6 evidence. This is not proof of continuous live Meta availability.

**Physics/scheduling:** deterministic M1/M3 fixture output, not real operational measurements.

**UI:** Next.js read-only dashboard and backend contract; real visual walkthrough pending owner's recorded evidence.
