"""Opt-in, loopback-only M4 demonstration endpoints with static local auth.

These endpoints MUST NOT be exposed to the internet: ephemeral single-process
state, static operator identity and no production session management.
"""
import hmac
import os
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import Field

from eden.sentinel.twin import TwinModel
from eden.sentinel.m3_demo import available_scenarios
from eden.sentinel.m3_scheduler import SchedulingPolicy
from eden.sentinel.m4_workflow import LocalApprovalWorkflow, ProposalView, WorkflowError

router = APIRouter(prefix="/m4", tags=["M4 local human approval demo"])
workflow = LocalApprovalWorkflow()


class CreateProposal(TwinModel):
    scenario: str = Field(min_length=1)
    policy: SchedulingPolicy = Field(default_factory=SchedulingPolicy)
    # Opt-in and billable: attach a live Muse Spark advisory for the human reader.
    # Refused unless the operator also set M4_ALLOW_LIVE_ADVISORY=1.
    live_advisory: bool = False


class OperatorStatus(TwinModel):
    mode: Literal["simulation"] = "simulation"
    operator_id: str
    live_advisory_enabled: bool


class HumanDecision(TwinModel):
    decision: str


def local_operator(request: Request, authorization: str | None = Header(default=None)) -> str:
    if os.getenv("M4_ENABLE_LOCAL_API") != "1":
        raise HTTPException(status_code=503, detail="M4 local approval API disabled")
    if request.client is None or request.client.host not in ("127.0.0.1", "::1", "testclient"):
        raise HTTPException(status_code=403, detail="loopback only")
    expected = os.getenv("M4_OPERATOR_TOKEN", "")
    actor = os.getenv("M4_OPERATOR_ID", "").strip()
    if len(expected) < 20 or not actor:
        raise HTTPException(status_code=503, detail="M4 operator configuration missing")
    provided = authorization.removeprefix("Bearer ") if authorization and authorization.startswith("Bearer ") else ""
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="operator token required")
    return actor


def translate_error(exc: WorkflowError) -> HTTPException:
    if exc.code in ("proposal_not_found", "unknown_scenario"):
        return HTTPException(status_code=404, detail=exc.code)
    if exc.code in ("guardian_rejected_plan", "plan_digest_mismatch",
                    "actual_simulation_safety_failure"):
        return HTTPException(status_code=422, detail=exc.code)
    return HTTPException(status_code=409, detail=exc.code)


def _live_advisory_enabled() -> bool:
    return os.getenv("M4_ALLOW_LIVE_ADVISORY") == "1"


def _live_advisory(scenario: str):
    """One billable two-request Muse Spark call; fails closed without a proposal."""
    if scenario not in available_scenarios():
        raise HTTPException(status_code=404, detail="unknown_scenario")
    # Lazy import: importing the API must never load the Model API adapter.
    from eden.sentinel import muse
    try:
        return muse.assess_m3_scenario(muse.build_meta_client(), scenario)
    except muse.ModelNotConfigured as exc:
        raise HTTPException(status_code=503, detail="advisory_not_configured") from exc
    except muse.ModelIntegrationError as exc:
        raise HTTPException(status_code=502, detail="advisory_unavailable") from exc


@router.get("/status", response_model=OperatorStatus)
def operator_status(operator: str = Depends(local_operator)):
    return OperatorStatus(operator_id=operator, live_advisory_enabled=_live_advisory_enabled())


@router.post("/proposals", response_model=ProposalView)
def create_proposal(body: CreateProposal, _operator: str = Depends(local_operator)):
    advisory = None
    if body.live_advisory:
        if not _live_advisory_enabled():
            raise HTTPException(status_code=403, detail="live_advisory_disabled")
        # The advisory's tool evidence is computed with the default policy.
        if body.policy != SchedulingPolicy():
            raise HTTPException(status_code=422, detail="advisory_requires_default_policy")
        advisory = _live_advisory(body.scenario)
    try:
        return workflow.create(body.scenario, policy=body.policy, advisory=advisory)
    except WorkflowError as exc:
        raise translate_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="invalid scheduling policy") from exc


@router.get("/proposals/{proposal_id}", response_model=ProposalView)
def get_proposal(proposal_id: str, _operator: str = Depends(local_operator)):
    try:
        return workflow.inspect(proposal_id)
    except WorkflowError as exc:
        raise translate_error(exc) from exc


@router.post("/proposals/{proposal_id}/decision", response_model=ProposalView)
def decide(proposal_id: str, body: HumanDecision, operator: str = Depends(local_operator)):
    try:
        return workflow.decide(proposal_id, operator=operator, decision=body.decision)
    except WorkflowError as exc:
        raise translate_error(exc) from exc


@router.post("/proposals/{proposal_id}/execute-simulation", response_model=ProposalView)
def simulate_application(proposal_id: str, operator: str = Depends(local_operator)):
    try:
        return workflow.apply_simulation(proposal_id, operator=operator)
    except WorkflowError as exc:
        raise translate_error(exc) from exc
