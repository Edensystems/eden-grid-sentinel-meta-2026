from __future__ import annotations

from datetime import datetime, timezone

from eden.integrations.rtdb import ref


class GuardianAgent:
    """Policy gate (kill switch, rate limit, allowed hours) backed by RTDB eden/guardian/*."""

    def __init__(self) -> None:
        self.state_ref = ref("eden/guardian/state")
        self.policy_ref = ref("eden/guardian/policies")
        self.log_ref = ref("eden/guardian/logs")

    def check_kill_switch(self) -> bool:
        return (self.state_ref.get() or {}).get("kill_switch", False)

    def rate_limit_ok(self, policies: dict) -> bool:
        last = self.state_ref.child("last_trigger").get()
        if not last or "max_agent_runs_per_min" not in policies:
            return True
        delta = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
        return delta > (60 / policies["max_agent_runs_per_min"])

    @staticmethod
    def validate_time_window(policies: dict) -> bool:
        if "allowed_hours" not in policies:
            return True
        start, end = policies["allowed_hours"]
        return start <= datetime.now().hour <= end

    def allow(self, agent_name: str) -> bool:
        policies = self.policy_ref.get() or {}

        if self.check_kill_switch():
            self.log(agent_name, "BLOCKED", "Kill switch active")
            return False
        if not self.rate_limit_ok(policies):
            self.log(agent_name, "BLOCKED", "Rate limit exceeded")
            return False
        if not self.validate_time_window(policies):
            self.log(agent_name, "BLOCKED", "Outside allowed hours")
            return False

        self.state_ref.update({"last_trigger": datetime.now(timezone.utc).isoformat()})
        self.log(agent_name, "ALLOWED", "All checks passed")
        return True

    def log(self, agent: str, decision: str, reason: str) -> None:
        self.log_ref.push({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "decision": decision,
            "reason": reason,
        })
