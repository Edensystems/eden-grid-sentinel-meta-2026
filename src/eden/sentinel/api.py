"""M0 health-only API: no hardware, simulation, or model calls."""
from fastapi import FastAPI

from eden.sentinel.schemas import HealthResponse

app = FastAPI(
    title="EDEN Grid Sentinel",
    version="0.0.1",
    description="Hackathon M0 scaffold. No real-world control endpoints.",
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="eden-grid-sentinel",
        phase="M0",
        data_mode="simulation",
    )
