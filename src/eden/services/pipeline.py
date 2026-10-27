"""
Shared Pub/Sub push handling for the think/learn/act Cloud Run services.

Every stage does the same thing: run its agent on the incoming event, persist
the result under eden/{community}/episodes/{senseId}, update the episode meta
status, and publish the result to the next topic.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from fastapi import FastAPI

from eden.core.logging import configure_logging, utc_now_iso
from eden.integrations.pubsub_io import publish_json
from eden.integrations.rtdb import update_meta, write_stage

log = logging.getLogger("eden")


def create_app(stage: str) -> FastAPI:
    configure_logging()
    app = FastAPI(title=f"eden-{stage}-service", version="0.2.0")

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


def safe_persist(community_id: str, sense_id: str, stage: str, data: Dict[str, Any] | None, meta: Dict[str, Any]) -> None:
    """Best-effort RTDB write; never fails the request. Skipped for events without a senseId."""
    if sense_id == "unknown":
        return
    try:
        if data is not None:
            write_stage(community_id, sense_id, stage, data)
        update_meta(community_id, sense_id, meta)
    except Exception as e:
        log.error(f"[{stage.upper()}] RTDB write failed | senseId={sense_id} | error={e}")


def run_stage(
    *,
    stage: str,
    run: Callable[[Dict[str, Any]], Dict[str, Any]],
    payload: Dict[str, Any],
    community_id: str,
    sense_id: str,
    ref_key: str,
    ref_id: str,
    build_event: Callable[[Dict[str, Any]], Dict[str, Any]],
    topic: str,
    publish_failure_ok: bool = False,
) -> Dict[str, Any]:
    tag = f"[{stage.upper()}]"

    try:
        result = run(payload)
        log.info(f"{tag} Agent completed | {ref_key}={ref_id}")
    except Exception as e:
        log.error(f"{tag} Agent failed | {ref_key}={ref_id} | error={e}")
        safe_persist(community_id, sense_id, stage, None,
                     {"status": f"{stage}_failed", f"{stage}_error": str(e), f"{stage}_at": utc_now_iso()})
        return {"ok": False, "stage": stage, ref_key: ref_id, "error": str(e)}

    event = build_event(result)
    safe_persist(community_id, sense_id, stage, event, {"status": f"{stage}_done", f"{stage}_at": utc_now_iso()})

    try:
        message_id = publish_json(topic, event, stage=stage)
        log.info(f"{tag} Published to {topic} | messageId={message_id} | {ref_key}={ref_id}")
        return {"ok": True, "published": topic, "messageId": message_id}
    except Exception as e:
        log.error(f"{tag} Publish failed | {ref_key}={ref_id} | error={e}")
        safe_persist(community_id, sense_id, stage, None,
                     {"status": f"{stage}_publish_failed", f"{stage}_publish_error": str(e)})
        if publish_failure_ok:
            return {"ok": True, "stage": stage, "warning": f"publish failed: {e}"}
        return {"ok": False, "stage": stage, ref_key: ref_id, "error": f"publish failed: {e}"}
