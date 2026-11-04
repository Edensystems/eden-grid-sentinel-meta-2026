# EDEN Grid Sentinel — Competition Submission Draft

**Working title:** EDEN Grid Sentinel: AI-Assisted Energy Resilience for Solar-Powered Schools

**Track:** Startup *only if this is the participant's confirmed registered track*.

**Theme:** Push the Frontier.

## Short description

EDEN Grid Sentinel is a simulation-first AI energy operator prototype for solar-powered schools. It combines a deterministic digital twin, transparent solar/load forecasts, constrained flexible-load scheduling, and Meta Muse Spark reasoning to identify predicted shortages and explain safe operational options. A Guardian independently checks simulation constraints and requires a human decision before applying any proposed change to the digital twin.

## Problem

Schools with limited solar and battery capacity must balance essential electrical needs against flexible activities when generation falls. Fixed schedules can consume energy that would be more valuable later, while purely verbal AI recommendations can be physically inconsistent or difficult to audit.

## Solution and technical execution

A Python/FastAPI microgrid simulator enforces battery state-of-charge, power and energy limits, conservation, and essential-load priority. A previous-day analogue forecast feeds bounded scheduling search; the selected plan is replayed against held-out synthetic solar, exposing prediction errors and flexible-load trade-offs. Muse Spark 1.3 uses a strictly allowlisted tool call to request local simulation data and produces a schema-validated, **advisory-only** risk assessment. The Guardian rechecks constraints independently; a named operator can approve or reject a plan for local simulation. A separate Next.js dashboard shows reproducible baseline-versus-scheduled outcomes in a read-only control room.

## Demonstrated evidence (synthetic only)

On the `critical_priority_school` fixture, baseline essential unmet demand is **1.7175 kWh** and scheduled essential unmet demand is **1.0000 kWh**, a **0.7175 kWh reduction**, while unmet flexible demand rises from **0** to **0.8770 kWh**. The simulation reports zero battery reserve violations. This is an illustrative trade-off, not field-validated energy savings. Additional scenarios and their exact outputs must be linked from the final M6 evidence artifact.

One documented owner-approved live Muse Spark 1.3 request (2026-10-31) completed with two model requests and one allowlisted M1 tool call, returning a human-approval-required advisory. The end-to-end M3→M4 agent interaction is tested offline with a deterministic fake transport. The dashboard does not invoke a live model or expose approval controls.

## Safety and limitations

No physical electrical system is connected or controlled. Forecasts are simple historical analogues, optimization is bounded local search, M4 approval/audit is in-memory for local demonstration, and SAM equipment segmentation inference is not claimed. The demonstration should not be represented as production-ready grid control.

## Links (fill only after verification)

- Source: https://github.com/Edensystems/eden-grid-sentinel-meta-2026
- Audited commit: **PENDING**
- Demo video: **PENDING**
- Public demo: **NOT CLAIMED** (localhost-only read-only preview)
- CI run + evaluation artifacts: **PENDING M6 SHA**

## Pre-submission checks

Review the exact submission fields, official rules, participating entity/team, source provenance and any required third-party licenses in the accepted-participant portal. Do not submit this draft without those checks.
