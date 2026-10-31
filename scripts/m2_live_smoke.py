"""M2 live smoke (opt-in only). No credentials or raw responses printed.

Dry-run by default. Live mode requires explicit two flags plus MODEL_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import sys

from eden.sentinel.muse import (ModelIntegrationError, assess_scenario,
                                build_meta_client)
from eden.sentinel.scenarios import build_scenario, scenario_names
from eden.sentinel.twin import run_simulation


def main() -> int:
    parser = argparse.ArgumentParser(description="EDEN M2 controlled smoke")
    parser.add_argument("--scenario", choices=scenario_names(), default="cloudy_school_day")
    parser.add_argument("--live", action="store_true", help="opt into billable Meta API calls")
    parser.add_argument("--confirm-billing", action="store_true", help="acknowledge at most two completions plus one transient retry per completion")
    args = parser.parse_args()
    if args.live != args.confirm_billing:
        parser.error("live mode requires BOTH --live and --confirm-billing")
    if not args.live:
        summary = run_simulation(build_scenario(args.scenario)).summary
        print(json.dumps({"mode": "offline_fixture", "scenario": args.scenario,
                          "summary": summary.model_dump(mode="json")}, indent=2))
        print("No Meta API request made. Live mode requires both flags.")
        return 0
    try:
        result = assess_scenario(build_meta_client(), args.scenario)
    except ModelIntegrationError as exc:
        print(f"M2 live smoke blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    print("Synthetic/advisory only; no action was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
