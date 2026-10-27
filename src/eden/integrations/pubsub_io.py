from __future__ import annotations

import base64
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, Tuple

from eden.core.config import settings

if TYPE_CHECKING:
    from google.cloud import pubsub_v1

log = logging.getLogger(__name__)

_publisher: "pubsub_v1.PublisherClient | None" = None


def decode_pubsub_push(envelope: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Pub/Sub push sends:
    {
      "message": { "data": "base64...", "attributes": {...} },
      "subscription": "..."
    }
    Returns (payload_dict, attributes_dict). Payload is {"raw": "..."} if not JSON.
    Never raises on bad input.
    """
    msg = envelope.get("message") or {}
    data_b64 = msg.get("data") or ""
    attributes = msg.get("attributes") or {}

    decoded = ""
    if data_b64:
        try:
            decoded = base64.b64decode(data_b64).decode("utf-8")
        except Exception as e:
            log.error(f"Pub/Sub base64 decode failed: {e}")
            return {}, attributes

    if decoded.strip():
        try:
            return json.loads(decoded), attributes
        except Exception:
            return {"raw": decoded}, attributes

    return {}, attributes


def get_publisher() -> "pubsub_v1.PublisherClient":
    global _publisher
    if _publisher is None:
        # Imported lazily: grpc is heavy and only needed when actually publishing
        from google.cloud import pubsub_v1


        _publisher = pubsub_v1.PublisherClient()
    return _publisher


def publish_json(topic_id: str, payload: Dict[str, Any], timeout: float = 10, **attributes: str) -> str:
    """Publish a JSON payload to a topic in the current project. Returns message_id."""
    if not settings.PROJECT_ID:
        raise RuntimeError("Missing PROJECT_ID env var (or GOOGLE_CLOUD_PROJECT/GCLOUD_PROJECT/GCP_PROJECT).")

    publisher = get_publisher()
    topic_path = publisher.topic_path(settings.PROJECT_ID, topic_id)
    future = publisher.publish(topic_path, json.dumps(payload).encode("utf-8"), **attributes)
    return future.result(timeout=timeout)
