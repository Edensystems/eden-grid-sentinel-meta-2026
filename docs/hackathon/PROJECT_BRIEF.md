# EDEN Grid Sentinel — Hackathon Project Brief

**Organization:** RavensAI  
**Existing program:** EDEN (Education, Energy and Nature)  
**Competition:** Meta Global AI Developer Hackathon 2026  
**Theme:** Push the Frontier  
**Track target:** Startup (subject to official eligibility)  
**Submission:** November 4, 2026, 9:00 PM ET (November 5, 2026, 05:00 EAT)

## One-sentence pitch
An AI-assisted solar microgrid operator that observes energy telemetry, anticipates shortages, safely plans load scheduling, and demonstrates outcomes in an auditable digital twin.

## Demo contract
A simulated school microgrid has a solar forecast shortfall. EDEN Sense receives structured telemetry; Muse Spark in Think invokes forecasting and optimization tools; Guardian checks deterministic feasibility and requires operator approval; Act applies the approved proposal in a digital twin; Learn logs forecasts and outcomes; dashboard compares intervention against a baseline.

## What it is NOT
- Not a live autonomous electrical switch controller.
- Not an agent-only optimization process without mathematical constraints.
- Not a whole-platform rewrite of EDEN.
- Not a scientifically validated fault detection tool based solely on segmented images.

## Metrics to report
Forecast MAE; load served (essential/nonessential); unmet demand (kWh); battery SoC violations; feasibility rate; tool call failures; latency; result relative to baseline. Report only measured or simulated values with clear labels.

## Architectural components
- Sense: meter readings, weather/solar forecast inputs (fixtures first).
- Think: Meta Muse Spark agent and tool calling.
- Guardian: deterministic safety/constraint validation and approval gate.
- Act: apply in simulator only.
- Learn: persist incident traces and compare expected versus observed outcomes.
- Visual Perception: SAM 3.1 panel/equipment segmentation, optional until core loop is stable.
- Dashboard: timeline, energy charts, incident analysis, approval, action outcome.

## Provenance / claims
The current repository must be inspected to determine which EDEN components are verified and what was developed during the competition. No deployed functionality should be claimed without a passing test or recorded operational evidence.

## Submission readiness
- [ ] Confirm participant acceptance and access to submission portal
- [ ] Read and accept official rules; verify existing-code eligibility
- [ ] Confirm Meta API credentials and quotas
- [ ] Working local and deployed demo
- [ ] Recorded baseline vs intervention experiment
- [ ] Tests and screenshots / screen capture
- [ ] Project README, architecture diagram, acknowledgments and attribution
- [ ] Submit by official deadline
