"""EDEN Sentinel API: M1 synthetic simulations, no external side effects."""
from fastapi import FastAPI, HTTPException
from eden.sentinel.schemas import HealthResponse
from eden.sentinel.scenarios import build_scenario, scenario_names
from eden.sentinel.twin import SimulationRequest, SimulationResult, run_simulation

app = FastAPI(
    title="EDEN Grid Sentinel", version="0.1.0",
    description="M1 simulated energy dispatch. No electrical control endpoints.",
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="eden-grid-sentinel",
                          phase="M0", data_mode="simulation")


@app.get("/sim/scenarios", response_model=list[str], tags=["digital-twin"])
def list_scenarios() -> list[str]:
    return scenario_names()


@app.get("/sim/scenarios/{name}", response_model=SimulationResult,
         tags=["digital-twin"])
def run_fixture(name: str) -> SimulationResult:
    try:
        scenario = build_scenario(name)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown simulation scenario")
    return run_simulation(scenario)


@app.post("/sim/run", response_model=SimulationResult, tags=["digital-twin"])
def run_custom(request: SimulationRequest) -> SimulationResult:
    return run_simulation(request)
