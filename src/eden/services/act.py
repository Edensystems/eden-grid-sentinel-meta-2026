from fastapi import Request

from eden.agents.act import ActAgent
from eden.core.config import settings
from eden.core.logging import utc_now_iso
from eden.integrations.pubsub_io import decode_pubsub_push
from eden.services.pipeline import create_app, log, run_stage

app = create_app("act")
agent = ActAgent()


@app.post("/pubsub/act")
async def pubsub_act(request: Request):
    payload, attributes = decode_pubsub_push(await request.json())

    community_id = payload.get("communityId") or settings.COMMUNITY_ID
    sense_id = payload.get("senseId") or "unknown"
    think_id = payload.get("thinkId") or "unknown"
    task_id = payload.get("taskId") or "unknown"
    log.info(f"[ACT] Received task event | taskId={task_id} | thinkId={think_id} | senseId={sense_id} | attrs={attributes}")

    return run_stage(
        stage="act",
        run=agent.run,
        payload=payload,
        community_id=community_id,
        sense_id=sense_id,
        ref_key="taskId",
        ref_id=task_id,
        topic=settings.TOPIC_ACT_ACTIONS,
        # Act is the last stage; the audit publish is optional, so don't fail the request
        publish_failure_ok=True,
        build_event=lambda result: {
            "communityId": community_id,
            "senseId": sense_id,
            "thinkId": think_id,
            "taskId": task_id,
            "actionId": f"action_{task_id}",
            "task": payload.get("task"),
            "actionResult": result,
            "timestamp": utc_now_iso(),
        },
    )
