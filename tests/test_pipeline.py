"""Offline smoke tests for the think/learn/act services (Firebase and Pub/Sub are stubbed)."""
import base64
import json

import pytest
from fastapi.testclient import TestClient

from eden.integrations import rtdb
from eden.services import pipeline


class FakeRef:
    def __init__(self, store, path):
        self.store, self.path = store, path

    def get(self):
        return None

    def set(self, data):
        self.store[self.path] = data

    def update(self, data):
        self.store.setdefault(self.path, {}).update(data)


@pytest.fixture
def env(monkeypatch):
    store, published = {}, []
    monkeypatch.setattr(rtdb, "ref", lambda path: FakeRef(store, path))
    monkeypatch.setattr(pipeline, "publish_json", lambda topic, event, **attrs: published.append((topic, event, attrs)) or "msg-1")
    return store, published


def push(payload):
    return {"message": {"data": base64.b64encode(json.dumps(payload).encode()).decode(), "attributes": {}}}


@pytest.mark.parametrize("stage,payload,topic", [
    ("think", {"senseId": "s1"}, "eden-think-output"),
    ("learn", {"senseId": "s1", "thinkId": "think_s1"}, "eden-learn-tasks"),
    ("act", {"senseId": "s1", "thinkId": "think_s1", "taskId": "task_think_s1"}, "eden-act-actions"),
])
def test_stage_persists_and_publishes(env, stage, payload, topic):
    store, published = env
    module = __import__(f"eden.services.{stage}", fromlist=["app"])

    resp = TestClient(module.app).post(f"/pubsub/{stage}", json=push(payload))

    assert resp.json() == {"ok": True, "published": topic, "messageId": "msg-1"}
    assert published[0][0] == topic and published[0][2] == {"stage": stage}
    assert store[f"eden/community_001/episodes/s1/{stage}"]["senseId"] == "s1"
    assert store["eden/community_001/episodes/s1/meta"]["status"] == f"{stage}_done"


def test_publish_failure_marks_meta(env, monkeypatch):
    store, _ = env

    def boom(*a, **k):
        raise RuntimeError("down")

    monkeypatch.setattr(pipeline, "publish_json", boom)
    from eden.services import learn

    resp = TestClient(learn.app).post("/pubsub/learn", json=push({"senseId": "s2", "thinkId": "t"}))

    assert resp.json()["ok"] is False
    assert store["eden/community_001/episodes/s2/meta"]["status"] == "learn_publish_failed"


def test_health(env):
    from eden.services import think

    assert TestClient(think.app).get("/health").json() == {"ok": True}
