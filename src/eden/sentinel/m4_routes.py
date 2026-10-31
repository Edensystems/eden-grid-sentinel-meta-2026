"""Opt-in, loopback-only M4 demonstration endpoints with static local auth.

These endpoints MUST NOT be exposed to the internet: ephemeral single-process
state, static operator identity and no production session management.
"""
import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import Field

from eden.sentinel.twin import TwinModel
from eden.sentinel.m3_scheduler import SchedulingPolicy
from eden.sentinel.m4_workflow import LocalApprovalWorkflow, ProposalView, WorkflowError

router = APIRouter(prefix="/m4", tags=["M4 local human approval demo"])
workflow = LocalApprovalWorkflow()


class CreateProposal(TwinModel):
    scenario: str = Field(min_length=1)
    policy: SchedulingPolicy = Field(default_factory=SchedulingPolicy)


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


@router.post("/proposals", response_model=ProposalView)
def create_proposal(body: CreateProposal, _operator: str = Depends(local_operator)):
    try:
        return workflow.create(body.scenario, policy=body.policy)
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
