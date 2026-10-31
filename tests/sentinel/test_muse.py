"""M2 tests: fake Meta endpoint, zero network, never load environment credentials."""
from __future__ import annotations

import json
from types import SimpleNamespace as NS

import pytest

from eden.sentinel.muse import (
    FINAL_MAX_COMPLETION_TOKENS, ModelIntegrationError, ModelNotConfigured, ModelProtocolError,
    _advice_schema, _parse_json_object, _tool_spec, assess_scenario,
    build_meta_client,
)
from eden.sentinel.scenarios import scenario_names

SCENARIO = "cloudy_school_day"


def initial_call(*, name="get_simulation_summary", args=None, finish="tool_calls", count=1, cid="call_1"):
    if args is None:
        args = json.dumps({"scenario_name": SCENARIO})
    calls = [NS(id=cid, function=NS(name=name, arguments=args)) for _ in range(count)]
    return NS(choices=[NS(finish_reason=finish, message=NS(tool_calls=calls, content=None))])


def advice_payload(**changes):
    payload = {
        "scenario_name": SCENARIO,
        "data_mode": "simulation",
        "risk_level": "high",
        "headline": "Energy shortage in synthetic school model",
        "explanation": "The synthetic fixture has unmet essential electricity demand.",
        "suggested_next_step": "Review flexible energy consumption and request operator approval.",
        "requires_human_approval": True,
    }
    payload.update(changes)
    return payload


def finish(payload=None, *, finish_reason="stop", tool_calls=None):
    return NS(choices=[NS(
        finish_reason=finish_reason,
        message=NS(tool_calls=tool_calls, content=json.dumps(payload or advice_payload())),
    )])


class FakeClient:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []
        self.chat = NS(completions=NS(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self.answers:
            raise AssertionError("Unexpected extra model request")
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer


def test_happy_path_reads_only_local_trusted_tool():
    client = FakeClient([initial_call(), finish()])
    outcome = assess_scenario(client, SCENARIO)
    assert outcome.mode == "simulation"
    assert outcome.kind == "advisory_only"
    assert outcome.tool_calls_executed == 1
    assert outcome.model_requests == 2
    assert outcome.evidence.source == "m1_deterministic_simulator"
    assert outcome.evidence.summary.unserved_essential_kwh == pytest.approx(2.4)
    assert outcome.assessment.requires_human_approval is True
    assert len(client.calls) == 2
    assert client.calls[0]["tool_choice"] == "auto"
    assert client.calls[0]["parallel_tool_calls"] is False
    assert client.calls[0]["store"] is False
    assert client.calls[1]["store"] is False
    assert "tools" not in client.calls[1]
    history = client.calls[1]["messages"]
    assert history[-2].tool_calls[0].id == "call_1"
    assert history[-1]["role"] == "tool"
    assert history[-1]["tool_call_id"] == "call_1"
    evidence = json.loads(history[-1]["content"])
    assert evidence["summary"]["final_soc_fraction"] == pytest.approx(0.2)
    assert client.calls[1]["response_format"]["json_schema"]["strict"] is True


def test_never_accept_unknown_scenario_or_call_provider():
    client = FakeClient([])
    with pytest.raises(ValueError):
        assess_scenario(client, "../../secrets")
    assert client.calls == []


@pytest.mark.parametrize("first", [
    initial_call(count=0),
    initial_call(finish="stop"),
    initial_call(count=2),
    initial_call(name="energize_relay"),
    initial_call(cid=""),
    initial_call(cid="x" * 65),
    initial_call(args='{"scenario_name": "night_reserve"}'),
    initial_call(args='{"scenario_name": "cloudy_school_day", "relay": "on"}'),
    initial_call(args='{"scenario_name": "cloudy_school_day", "scenario_name": "cloudy_school_day"}'),
    initial_call(args='not a json object'),
    initial_call(args='[1,2]'),
    initial_call(args='{"scenario_name": 45}'),
])
def test_rejects_invalid_tool_calls_without_second_request(first):
    client = FakeClient([first])
    with pytest.raises(ModelProtocolError):
        assess_scenario(client, SCENARIO)
    assert len(client.calls) == 1


def test_invalid_final_schema_fails_closed():
    client = FakeClient([initial_call(), finish(advice_payload(requires_human_approval=False))])
    with pytest.raises(ModelProtocolError):
        assess_scenario(client, SCENARIO)
    assert len(client.calls) == 2


@pytest.mark.parametrize("bad_final", [
    advice_payload(scenario_name="night_reserve"),
    advice_payload(data_mode="measured"),
    advice_payload(risk_level="critical"),
    advice_payload(unknown_extra=True),
    advice_payload(headline=""),
    advice_payload(explanation=""),
])
def test_invalid_model_assessment_is_not_accepted(bad_final):
    with pytest.raises(ModelProtocolError):
        assess_scenario(FakeClient([initial_call(), finish(bad_final)]), SCENARIO)


def test_incomplete_final_or_tool_call_rejected():
    client = FakeClient([initial_call(), finish(finish_reason="length")])
    with pytest.raises(ModelProtocolError):
        assess_scenario(client, SCENARIO)
    client = FakeClient([initial_call(), finish(tool_calls=[NS(id="evil")])])
    with pytest.raises(ModelProtocolError):
        assess_scenario(client, SCENARIO)


@pytest.mark.parametrize("reason,label", [
    ("length", "length"), ("content_filter", "content_filter"),
    ("ignore previous instructions", "other"), (None, "other"),
])
def test_incomplete_final_names_only_allowlisted_reason(reason, label):
    client = FakeClient([initial_call(), finish(finish_reason=reason)])
    with pytest.raises(ModelProtocolError) as exc:
        assess_scenario(client, SCENARIO)
    assert str(exc.value) == f"final model response was not completed (finish_reason={label})"


def test_final_request_uses_raised_token_budget():
    client = FakeClient([initial_call(), finish()])
    assess_scenario(client, SCENARIO)
    assert client.calls[1]["max_completion_tokens"] == FINAL_MAX_COMPLETION_TOKENS == 4096
    assert client.calls[0]["max_completion_tokens"] == 768


def test_retry_only_transient_status_once(monkeypatch):
    monkeypatch.setattr("eden.sentinel.muse.time.sleep", lambda seconds: None)
    transient = RuntimeError("private-provider-error")
    transient.status_code = 429
    client = FakeClient([transient, initial_call(), finish()])
    result = assess_scenario(client, SCENARIO)
    assert result.mode == "simulation"
    assert len(client.calls) == 3  # 1 retry + 2 logical turns


def test_persistent_transient_error_sanitized(monkeypatch):
    monkeypatch.setattr("eden.sentinel.muse.time.sleep", lambda seconds: None)
    err = RuntimeError("sensitive-token-should-not-be-shown")
    err.status_code = 503
    client = FakeClient([err, err])
    with pytest.raises(ModelIntegrationError) as excinfo:
        assess_scenario(client, SCENARIO)
    assert "sensitive-token" not in str(excinfo.value)
    assert len(client.calls) == 2


def test_auth_error_no_retry_and_sanitized():
    err = RuntimeError("bearer-secret")
    err.status_code = 401
    client = FakeClient([err])
    with pytest.raises(ModelIntegrationError) as excinfo:
        assess_scenario(client, SCENARIO)
    assert "bearer-secret" not in str(excinfo.value)
    assert len(client.calls) == 1


def test_missing_meta_api_key_fails_before_openai_import(monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with pytest.raises(ModelNotConfigured):
        build_meta_client()


def test_closed_tool_schema_matches_scenarios():
    definition = _tool_spec()
    params = definition["function"]["parameters"]
    assert params["additionalProperties"] is False
    assert sorted(params["properties"]["scenario_name"]["enum"]) == scenario_names()
    format_ = _advice_schema()
    fields = format_["json_schema"]["schema"]
    assert fields["additionalProperties"] is False
    assert sorted(fields["required"]) == sorted(fields["properties"])


def test_reject_json_duplicate_keys_and_oversized_payload():
    with pytest.raises(ModelProtocolError):
        _parse_json_object('{"a":1,"a":2}')
    with pytest.raises(ModelProtocolError):
        _parse_json_object("{" + " " * 4100 + "}")
