from fastapi import Request

from eden.agents.learn import LearnAgent
from eden.core.config import settings
from eden.core.logging import utc_now_iso
from eden.integrations.pubsub_io import decode_pubsub_push
from eden.services.pipeline import create_app, log, run_stage

app = create_app("learn")
agent = LearnAgent()


@app.post("/pubsub/learn")
async def pubsub_learn(request: Request):
    payload, attributes = decode_pubsub_push(await request.json())

    community_id = payload.get("communityId") or settings.COMMUNITY_ID
    sense_id = payload.get("senseId") or "unknown"
    think_id = payload.get("thinkId") or "unknown"
    log.info(f"[LEARN] Received think event | thinkId={think_id} | senseId={sense_id} | attrs={attributes}")

    return run_stage(
        stage="learn",
        run=agent.run,
        payload=payload,
        community_id=community_id,
        sense_id=sense_id,
        ref_key="thinkId",
        ref_id=think_id,
        topic=settings.TOPIC_LEARN_TASKS,
        build_event=lambda result: {
            "communityId": community_id,
            "senseId": sense_id,
            "thinkId": think_id,
            "taskId": f"task_{think_id}",
            "task": result,
            "timestamp": utc_now_iso(),
        },
    )
