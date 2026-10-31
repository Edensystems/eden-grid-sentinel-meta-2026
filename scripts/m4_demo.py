"""Offline no-network M4 demo. Explicit decision is mandatory."""
import argparse
import json
from eden.sentinel.m4_workflow import LocalApprovalWorkflow


def main():
    parser = argparse.ArgumentParser(description="EDEN M4 local approval demo")
    parser.add_argument("--scenario", default="critical_priority_school")
    parser.add_argument("--operator", default="demo-operator")
    parser.add_argument("--decision", choices=["approved", "rejected"])
    parser.add_argument("--apply-simulation", action="store_true")
    args = parser.parse_args()
    system = LocalApprovalWorkflow()
    proposed = system.create(args.scenario)
    print("PROPOSAL", json.dumps(proposed.model_dump(mode="json"), indent=2))
    decision = args.decision or input("Human operator decision (approved/rejected): ").strip()
    if args.apply_simulation and decision != "approved":
        parser.error("cannot apply a rejected proposal")
    decided = system.decide(proposed.proposal_id, operator=args.operator, decision=decision)
    print("DECISION", json.dumps(decided.model_dump(mode="json"), indent=2))
    if args.apply_simulation:
        applied = system.apply_simulation(proposed.proposal_id, operator=args.operator)
        assert system.verify_audit(applied.audit)
        print("APPLIED_TO_SYNTHETIC_TWIN", json.dumps(applied.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
