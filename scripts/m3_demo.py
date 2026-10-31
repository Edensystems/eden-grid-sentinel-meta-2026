"""Offline M3 demo. Invoke: python scripts/m3_demo.py --scenario cloudy_school_day"""
import argparse
import json
from eden.sentinel.m3_demo import evaluate_fixture, available_scenarios


def main():
    parser = argparse.ArgumentParser(description="EDEN M3 synthetic energy scheduling")
    parser.add_argument("--scenario", default="cloudy_school_day",
                        choices=available_scenarios())
    parser.add_argument("--json", action="store_true", help="emit entire result JSON")
    args = parser.parse_args()
    outcome = evaluate_fixture(args.scenario)
    realized_baseline = outcome.realized.baseline.summary
    realized_scheduled = outcome.realized.scheduled.summary
    if args.json:
        print(outcome.model_dump_json(indent=2))
    else:
        print(json.dumps({
            "data_mode": outcome.mode,
            "scenario": outcome.scenario,
            "forecast_method": outcome.forecast.method,
            "solar_forecast_mae_kw": outcome.forecast.metrics.solar_mae_kw,
            "schedule_method": outcome.scheduling.method,
            "status": outcome.scheduling.status,
            "essential_unserved_baseline_kwh": realized_baseline.unserved_essential_kwh,
            "essential_unserved_scheduled_kwh": realized_scheduled.unserved_essential_kwh,
            "flexible_unserved_baseline_kwh": realized_baseline.unserved_flexible_kwh,
            "flexible_unserved_scheduled_kwh": realized_scheduled.unserved_flexible_kwh,
            "shifted_kwh": outcome.scheduling.summary.energy_shifted_kwh,
            "reserve_violations": outcome.realized.battery_reserve_violations,
        }, indent=2))


if __name__ == "__main__":
    main()
