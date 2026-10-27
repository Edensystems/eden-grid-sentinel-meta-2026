from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timezone

from eden.core.config import settings
from eden.integrations.pubsub_io import publish_json
from eden.integrations.rtdb import community_path, ref


class SenseAgent:
    """Simulated sensor: writes readings to RTDB and publishes them to the sense topic."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.db_ref = ref(community_path("sense_data"))

    def _build_payload(self) -> dict:
        return {
            "communityId": settings.COMMUNITY_ID,
            "senseId": f"sense_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signals": {
                "temperature_c": round(random.uniform(18.0, 35.0), 2),
                "humidity_pct": round(random.uniform(30.0, 80.0), 2),
                "energy_usage_kw": round(random.uniform(0.5, 10.0), 2),
            },
            "meta": {
                "agent_id": self.agent_id,
                "source": "simulation",
                "schema": "eden.sense.v1",
            },
        }

    async def collect_data(self) -> None:
        payload = self._build_payload()

        self.db_ref.push(payload)
        print(f"[SENSE] Saved to Firebase | senseId={payload['senseId']}")

        message_id = publish_json(
            settings.TOPIC_SENSE_EVENTS,
            payload,
            timeout=30,
            senseId=payload["senseId"],
            communityId=payload["communityId"],
            source=payload["meta"]["source"],
        )
        print(f"[SENSE] Published to Pub/Sub | messageId={message_id} | senseId={payload['senseId']}")

    async def stream_data(self, interval: int = 5) -> None:
        print("[SENSE] Agent started")
        while True:
            try:
                await self.collect_data()
            except Exception as e:
                print("[SENSE] ERROR:", e)
            await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(SenseAgent(agent_id="sense_agent_001").stream_data(interval=10))
