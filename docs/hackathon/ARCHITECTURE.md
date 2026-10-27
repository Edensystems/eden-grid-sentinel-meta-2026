# Planned architecture and trust boundaries

## High-level target (M1–M5; **not implemented yet**)

```text
Telemetry fixture / digital twin (untrusted inputs)
              |
              v
      Sense: typed ingestion -----> audit log
              |
              v
 Think: Muse Spark reasoning <--> typed forecast + optimization tools
              |
              v
 Guardian: deterministic constraints, permissions and policy checks
              |
              v
       Human approve/reject
              |
              v
   Act: apply to simulator ONLY
              |
              v
    Learn: event results and baseline comparison
              |
              v
       Dashboard / evaluation
```

## M0 implemented runtime

`FastAPI GET /health` only (`eden.sentinel.api`). Pydantic model definitions are contracts; there are NO telemetry ingestion endpoints or actions.

The pre-existing EDEN Pub/Sub pipeline (`eden.services.think|learn|act`) lives in the same repository but is not wired to Sentinel; see `BASELINE.md`.

## Contracts v1.0

- `TelemetryEvent`: `event_id`, `site_id`, timezone-aware `observed_at`, `source`, nonnegative solar/essential/flexible power in kW, battery SOC fraction [0,1], capacity in kWh (>0).
- `ForecastEvent`: timestamped horizon points with nonnegative solar and load predictions in kW; source label may be `modeled`.
- `RecommendationEvent`: typed proposal to shift flexible load or take no action, proposed shift energy in kWh, `approval_required=true`.
- `ApprovalEvent`: recommendation linkage, named operator identity, approve/reject, timezone-aware time.
- `ExecutionAuditEvent`: linkage to proposal + approval, immutable intent for logging, mode restricted to `simulation`, outcome and event time.

JSON events MUST be validated at all trust boundaries. Times are ISO 8601 with timezone; energy kWh and power kW must not be confused. Explicit versioning (`schema_version='1.0'`) enables evolution.

## Security boundaries

1. External inputs are untrusted; schemas reject extra fields and invalid basic ranges.
2. LLM reasoning output is advisory and **never** a privileged command. Deterministic tools own numerical results.
3. Guardian must validate physical limits and essential-load preservation separately from the LLM.
4. No real-world controls. Act sends only to an in-memory or sandbox simulator.
5. Even simulator actions require an approval token or audit-backed operator identity in M4 onward.
6. Audit records distinguish observed measured data from simulation or predicted values.
7. API tokens reside only in local environment or cloud secret manager, not Git.

**Limits of M0 validation:** Schemas alone are not a working Guardian or authorization system. The M0 `HealthResponse` and contracts make no safety guarantee for future runtime code.
