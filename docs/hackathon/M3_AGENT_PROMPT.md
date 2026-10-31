# M3 Coding Agent Instructions — EDEN Grid Sentinel

You are engineering orchestrator of the accepted Meta hackathon entry EDEN Grid Sentinel.

Read `AGENTS.md`, `docs/hackathon/BASELINE.md`, `docs/hackathon/M1_REPORT.md`, and the supplied `docs/hackathon/M3_RUNBOOK.md` and `M3_REPORT.md`; read M2 report if present.

1. Inspect current Git branch/status/CI; preserve all user changes. The upstream M1 PR was an unmerged draft and M2 was not published when this patch was authored. Do not overwrite local M2 files.
2. Integrate M3 on an isolated `feat/m3-forecast-scheduler` branch based on reviewed M1 source or newer reconciled branch. Merge safely if API or tests changed.
3. Run complete test suites on Python 3.11 and 3.12, verify M1 and M2 backwards compatibility, and verify M3's synthetic scenario API using real loopback HTTP.
4. Verify planning uses prior-day synthetic solar forecast and declared demand timetable, **never future actual solar**. Score held-out actual outcomes separately and surface losses if the forecast leads to worse performance.
5. Verify all retiming, energy, battery reserve, essential-priority, finite-value, timeout and algorithm-complexity limits. This is bounded local search, not a certified globally optimal solver.
6. Ensure no Meta model calls, cloud service writes, paid operations, credential disclosure or actual electrical controls.
7. Refresh `M3_REPORT.md` with exact SHA, tests, CI URLs, metrics and limitations. Publish an isolated draft PR and stop for the owner review. Do NOT merge, begin M4, or claim prior M0/M1/M2 gates have been closed unless explicitly documented.
