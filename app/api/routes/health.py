from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return the service health status."""
    return HealthResponse(
        status="ok",
        service="game-test-platform",
        version="0.1.0",
    )
