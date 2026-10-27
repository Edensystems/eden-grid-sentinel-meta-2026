from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from eden.integrations.rtdb import community_path, ref


class ActAgent:
    """Converts THINK predictions into actionable plans."""

    def __init__(self) -> None:
        self.think_ref = ref(community_path("think_output"))
        self.act_ref = ref(community_path("act", "actions"))

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: derive the action from payload["task"].
        return {"message": "Act..."}

    def fetch_predictions(self):
        return self.think_ref.get() or []

    @staticmethod
    def interpret_prediction(prediction: str) -> Dict[str, Any]:
        action = {
            "action_id": str(uuid.uuid4()),
            "type": "info",
            "description": "Monitor system metrics",
            "priority": "low",
            "target_role": "Community_Admin",
            "source_prediction": prediction,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if "energy" in prediction.lower():
            action.update(
                type="advisory",
                description="Shift non-critical operations to off-peak hours",
                priority="high",
                target_role="SME_Manager",
            )
        return action

    def create_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        self.act_ref.child(action["action_id"]).set(action)
        return action


if __name__ == "__main__":
    agent = ActAgent()
    for pred in agent.fetch_predictions():
        print("Created Action:", agent.create_action(agent.interpret_prediction(pred)))
