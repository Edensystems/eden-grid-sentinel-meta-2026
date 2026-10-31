"""M5 limited staging ASGI app: read-only synthetic energy demo.

It deliberately imports neither M2 model calls nor M4 approval routes. It must
NOT be mistaken for the production control interface or a live energy feed.
"""
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from eden.sentinel.m3_demo import M3Evaluation, available_scenarios, evaluate_fixture


class PreviewHealth(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["eden-grid-sentinel"] = "eden-grid-sentinel"
    phase: Literal["M5_PREVIEW"] = "M5_PREVIEW"
    data_mode: Literal["simulation"] = "simulation"
    control_mode: Literal["read_only"] = "read_only"


app = FastAPI(
    title="EDEN Grid Sentinel — Read-Only M5 Preview",
    version="0.5.0",
    description="Synthetic microgrid comparison. No AI calls, approval endpoints, writes, or physical control.",
)


@app.get("/health", response_model=PreviewHealth)
def health() -> PreviewHealth:
    return PreviewHealth()


@app.get("/m3/scenarios", response_model=list[str])
def scenarios() -> list[str]:
    return available_scenarios()


@app.get("/m3/evaluate/{scenario}", response_model=M3Evaluation)
def evaluate(scenario: str) -> M3Evaluation:
    if scenario not in available_scenarios():
        raise HTTPException(status_code=404, detail="unknown synthetic scenario")
    return evaluate_fixture(scenario)
