"""M2 integration checks added during verification: retry ceiling, credential
isolation, offline-by-default smoke script and no billable HTTP route.

Uses the fake client from test_muse; never contacts Meta and never needs a key.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from eden.sentinel import muse
from eden.sentinel.muse import ModelIntegrationError, assess_scenario

from test_muse import SCENARIO, FakeClient, finish, initial_call

ROOT = Path(__file__).resolve().parents[2]
FAKE_KEY = "fake-key-for-isolation-test-0000"


def transient(status: int = 503) -> RuntimeError:
    err = RuntimeError("provider detail")
    err.status_code = status
    return err


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr("eden.sentinel.muse.time.sleep", lambda seconds: None)


def test_retry_ceiling_is_four_provider_calls_across_both_turns():
    client = FakeClient([transient(), initial_call(), transient(429), finish()])
    result = assess_scenario(client, SCENARIO)
    assert result.assessment.requires_human_approval is True
    assert len(client.calls) == 4
    assert "tools" in client.calls[0] and "tools" in client.calls[1]
    assert "response_format" in client.calls[2] and "response_format" in client.calls[3]


def test_final_turn_persistent_transient_error_stops_after_one_retry():
    client = FakeClient([initial_call(), transient(), transient()])
    with pytest.raises(ModelIntegrationError):
        assess_scenario(client, SCENARIO)
    assert len(client.calls) == 3


def test_non_transient_exception_is_not_retried():
    client = FakeClient([ValueError("bad request body")])
    with pytest.raises(ModelIntegrationError) as excinfo:
        assess_scenario(client, SCENARIO)
    assert len(client.calls) == 1
    assert excinfo.value.__cause__ is None and excinfo.value.__suppress_context__


def test_environment_key_never_enters_requests(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", FAKE_KEY)
    client = FakeClient([initial_call(), finish()])
    assess_scenario(client, SCENARIO)
    assert FAKE_KEY not in json.dumps(client.calls, default=repr)


def test_live_client_has_meta_base_url_and_no_sdk_retries(monkeypatch):
    pytest.importorskip("openai")
    monkeypatch.setenv("MODEL_API_KEY", FAKE_KEY)
    client = muse.build_meta_client(timeout_seconds=7.0)
    assert str(client.base_url).rstrip("/") == muse.BASE_URL
    assert client.max_retries == 0
    assert client.timeout == 7.0
    assert FAKE_KEY not in repr(client)


def test_blank_key_is_treated_as_missing(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "   ")
    with pytest.raises(muse.ModelNotConfigured):
        muse.build_meta_client()


def test_import_loads_no_sdk_and_api_does_not_import_adapter():
    code = (
        "import sys, eden.sentinel.api\n"
        "assert 'eden.sentinel.muse' not in sys.modules\n"
        "import eden.sentinel.muse\n"
        "assert 'openai' not in sys.modules\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "MODEL_API_KEY"}
    env["PYTHONPATH"] = str(ROOT / "src")
    subprocess.run([sys.executable, "-c", code], check=True, cwd=ROOT, env=env)


def test_http_api_exposes_no_model_route():
    from eden.sentinel.api import app

    paths = {getattr(route, "path", "") for route in app.routes}
    for word in ("muse", "model", "assess", "advis", "meta", "llm"):
        assert not any(word in path.lower() for path in paths), paths


def _load_smoke():
    spec = importlib.util.spec_from_file_location("m2_live_smoke", ROOT / "scripts" / "m2_live_smoke.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_smoke_is_offline_by_default(monkeypatch, capsys):
    smoke = _load_smoke()
    monkeypatch.setattr(smoke, "build_meta_client", lambda: pytest.fail("client built"))
    monkeypatch.setattr(sys, "argv", ["m2_live_smoke.py", "--scenario", SCENARIO])
    assert smoke.main() == 0
    out = capsys.readouterr().out
    assert '"mode": "offline_fixture"' in out
    assert "No Meta API request made" in out


@pytest.mark.parametrize("flags", [["--live"], ["--confirm-billing"]])
def test_smoke_requires_both_live_flags(monkeypatch, flags):
    smoke = _load_smoke()
    monkeypatch.setattr(smoke, "build_meta_client", lambda: pytest.fail("client built"))
    monkeypatch.setattr(sys, "argv", ["m2_live_smoke.py", *flags])
    with pytest.raises(SystemExit) as excinfo:
        smoke.main()
    assert excinfo.value.code == 2


def test_smoke_live_without_key_exits_nonzero_without_request(monkeypatch, capsys):
    smoke = _load_smoke()
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["m2_live_smoke.py", "--live", "--confirm-billing"])
    assert smoke.main() == 1
    assert "MODEL_API_KEY is not configured" in capsys.readouterr().err
