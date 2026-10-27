from __future__ import annotations

from typing import Any, Dict

import firebase_admin
from firebase_admin import db

from eden.core.config import settings


def init_firebase() -> None:
    """
    Initialize firebase_admin once, using Application Default Credentials
    (attached service account on Cloud Run; GOOGLE_APPLICATION_CREDENTIALS locally).
    """
    if firebase_admin._apps:
        return
    if not settings.FIREBASE_DB_URL:
        raise RuntimeError("Missing FIREBASE_DB_URL env var")
    firebase_admin.initialize_app(options={"databaseURL": settings.FIREBASE_DB_URL})


def ref(path: str) -> db.Reference:
    init_firebase()
    return db.reference(path)


def community_path(*parts: str, community_id: str | None = None) -> str:
    return "/".join(["eden", community_id or settings.COMMUNITY_ID, *parts])


def write_stage(community_id: str, sense_id: str, stage: str, data: Dict[str, Any]) -> None:
    ref(community_path("episodes", sense_id, stage, community_id=community_id)).set(data)


def update_meta(community_id: str, sense_id: str, meta: Dict[str, Any]) -> None:
    ref(community_path("episodes", sense_id, "meta", community_id=community_id)).update(meta)
