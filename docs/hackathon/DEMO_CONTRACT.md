# Reproducible demo contract (future milestones)

## Demo input

A synthetic school energy system with hourly solar, essential load, flexible load, and battery measurements (kW, kWh, SOC). A forecast predicts supply shortage over a known interval. All inputs are declared **simulated** and seeded for reproducibility.

## Demo event chain

1. Sensor fixture publishes a typed telemetry event.
2. Muse Spark agent interprets alerts and invokes deterministic forecasting and optimization tools.
3. Guardian validates every proposed plan against battery and essential-load constraints.
4. An identified human operator explicitly approves or rejects proposal.
5. Approved plan is applied **only to the digital twin**.
6. System measures (a) unchanged-operation baseline vs (b) intervention, with visible incident/audit trace.
7. Optional SAM 3.1 segments visible solar hardware imagery to aid equipment inventory; do not call this fault diagnosis.

## Required measurement evidence

Report unmet essential load (kWh), total demand served, reserve violations, forecast MAE, tool failures and latency based on actually run experiments. Reject missing data or false precision. Avoid claims of field savings without measured field data.

## M0 acceptance

No full demo yet. M0 passes on health-check verification, typed schema tests, CI, secure provenance documentation, and an approved architecture; the workflow is a planned milestone only.
