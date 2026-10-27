from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from eden.integrations.rtdb import community_path, ref


class LearnAgent:
    """Turns THINK signals into learning tasks."""

    def __init__(self) -> None:
        self.think_ref = ref(community_path("think_output"))
        self.learn_ref = ref(community_path("learn", "tasks"))

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: derive the task from payload["thinkResult"].
        return {"message": "Learning..."}

    def fetch_think_signals(self):
        return self.think_ref.get() or []

    def generate_learning_task(self, signal: str) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "objective": self.map_objective(signal),
            "skill": self.map_skill(signal),
            "source_signal": signal,
            "difficulty": self.estimate_difficulty(signal),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.learn_ref.child(task_id).set(task)
        return task

    @staticmethod
    def map_objective(signal: str) -> str:
        if "energy" in signal.lower():
            return "Understand and optimize energy consumption patterns"
        if "water" in signal.lower():
            return "Detect and respond to water system inefficiencies"
        return "Interpret system data for operational decision-making"

    @staticmethod
    def map_skill(signal: str) -> str:
        if "energy" in signal.lower():
            return "Energy Management"
        if "anomaly" in signal.lower():
            return "System Diagnostics"
        return "Data Literacy"

    @staticmethod
    def estimate_difficulty(signal: str) -> str:
        return "medium" if "optimize" in signal.lower() else "beginner"


if __name__ == "__main__":
    agent = LearnAgent()
    for signal in agent.fetch_think_signals():
        print("Generated Learning Task:", agent.generate_learning_task(signal))
