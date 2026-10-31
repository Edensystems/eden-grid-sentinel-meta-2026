"""Read-only M3 simulation comparison endpoints; no billable/cloud/actuation calls."""
from fastapi import APIRouter, HTTPException
from eden.sentinel.m3_demo import M3Evaluation, evaluate_fixture, available_scenarios
from eden.sentinel.m3_scheduler import SchedulingPolicy

router = APIRouter(prefix="/m3", tags=["M3 forecasts and scheduling"])


@router.get("/scenarios", response_model=list[str])
def list_available_scenarios():
    return available_scenarios()


@router.get("/evaluate/{name}", response_model=M3Evaluation)
def evaluate(name: str):
    try:
        return evaluate_fixture(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/evaluate/{name}", response_model=M3Evaluation)
def evaluate_with_policy(name: str, policy: SchedulingPolicy):
    try:
        return evaluate_fixture(name, policy)
    except ValueError as exc:
        # Invalid policy *against* a specific scenario, not a missing fixture.
        if name not in available_scenarios():
            raise HTTPException(status_code=404, detail="unknown synthetic scenario") from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc
