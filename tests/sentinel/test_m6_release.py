"""M6 offline evaluation and submission evidence tests (no service/network calls)."""
import copy
import json
from pathlib import Path
import pytest

from eden.sentinel.m3_demo import available_scenarios
from eden.sentinel.m5_readonly import app
from scripts.m6_evidence import generate_evidence, write_evidence


def test_release_report_has_all_scenarios_and_deterministic_fingerprint():
    first=generate_evidence(use_mock_muse=True)
    second=generate_evidence(use_mock_muse=True)
    assert first == second
    assert len(first["scenarios"]) == len(available_scenarios()) == 4
    assert first["meta_inference"] == "FAKE_CLIENT_ONLY"
    assert first["data_mode"] == "simulation"
    assert len(first["sha256_canonical"])==64


def test_incident_enforces_rejection_approval_and_audit():
    proof=generate_evidence(use_mock_muse=True)["incident"]
    assert proof["proposal_rejection_enforced"]
    assert proof["single_application_enforced"]
    assert proof["guardian_approved_plan"]
    assert proof["audit_chain_verified"]
    assert proof["tampered_plan_denied_by_guardian"]
    # Refused execution attempts are part of the verified hash chain.
    assert proof["rejected_event_types"] == ["proposed", "rejected", "denied"]
    assert proof["approved_event_types"] == ["proposed", "approved", "applied", "denied"]
    assert proof["realized_essential_reduction_kwh"] == pytest.approx(0.7175)
    assert proof["realized_flexible_unserved_kwh"] == pytest.approx(0.877)
    assert proof["operator_auth"] == "local_demonstration_only"


def test_every_scenario_reports_consistent_tradeoffs_and_bounds():
    rows=generate_evidence(use_mock_muse=True)["scenarios"]
    for row in rows:
        assert row["reserve_violations"]==0
        assert row["max_abs_bus_residual_kwh"] <= 1e-8
        assert row["essential_baseline_unserved_kwh"] >=0
        assert row["essential_scheduled_unserved_kwh"] >=0
        assert row["flexible_baseline_unserved_kwh"] >=0
        assert row["flexible_scheduled_unserved_kwh"] >=0
        assert row["essential_unserved_reduction_kwh"] == pytest.approx(
            row["essential_baseline_unserved_kwh"]-row["essential_scheduled_unserved_kwh"],abs=1e-6)
        assert row["flexible_unserved_reduction_kwh"] == pytest.approx(
            row["flexible_baseline_unserved_kwh"]-row["flexible_scheduled_unserved_kwh"],abs=1e-6)


def test_no_approval_or_control_routes_on_public_preview():
    paths=app.openapi()["paths"]
    assert set(paths)=={"/health","/m3/scenarios","/m3/evaluate/{scenario}"}
    assert all(set(ops)=={"get"} for ops in paths.values())


def test_written_artifact_is_valid_json_and_explicitly_synthetic(tmp_path):
    report=generate_evidence(use_mock_muse=True)
    write_evidence(tmp_path,report)
    actual=json.loads((tmp_path/"m6_evidence.json").read_text(encoding="utf-8"))
    assert actual==report
    md=(tmp_path/"m6_evidence.md").read_text(encoding="utf-8")
    assert "Synthetic simulation" in md
    assert "fake model" in md.lower()
    assert report["sha256_canonical"] in md
    assert not any(name in md for name in ("MODEL_API_KEY=", "sk-proj-", "LLM_"))
