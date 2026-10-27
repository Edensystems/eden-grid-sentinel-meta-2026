from fastapi import Request

from eden.agents.think import ThinkAgent
from eden.core.config import settings
from eden.core.logging import utc_now_iso
from eden.integrations.pubsub_io import decode_pubsub_push
from eden.services.pipeline import create_app, log, run_stage, safe_persist

app = create_app("think")
agent = ThinkAgent()


@app.post("/pubsub/think")
async def pubsub_think(request: Request):
    payload, attributes = decode_pubsub_push(await request.json())

    community_id = payload.get("communityId") or settings.COMMUNITY_ID
    sense_id = payload.get("senseId") or attributes.get("senseId") or "unknown"
    log.info(f"[THINK] Received sense event | senseId={sense_id} | attrs={attributes}")

    # Persist the raw sense event that started this episode
    if payload:
        safe_persist(community_id, sense_id, "sense", payload, {"status": "sense_received", "sense_at": utc_now_iso()})

    return run_stage(
        stage="think",
        run=agent.run,
        payload=payload,
        community_id=community_id,
        sense_id=sense_id,
        ref_key="senseId",
        ref_id=sense_id,
        topic=settings.TOPIC_THINK_OUTPUT,
        build_event=lambda result: {
            "communityId": community_id,
            "senseId": sense_id,
            "thinkId": f"think_{sense_id}",
            "thinkResult": result,
            "timestamp": utc_now_iso(),
        },
    )
