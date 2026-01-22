"""
Health check endpoints.
"""

from datetime import datetime

from fastapi import APIRouter

from app.config import settings
from app.dependencies import SupabaseDep
from app.models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(supabase: SupabaseDep) -> HealthResponse:
    """
    Health check endpoint for monitoring.

    Returns overall system health and status of dependencies.
    """
    # Check database connectivity
    db_status = "up" if await supabase.health_check() else "down"

    # LLM status (assume up if configured)
    llm_status = "up" if settings.openai_api_key else "configured"

    # Overall status
    overall_status = "healthy" if db_status == "up" else "unhealthy"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat() + "Z",
        services={
            "database": db_status,
            "llm": llm_status,
        },
    )


@router.get("/health/live")
async def liveness_probe() -> dict[str, str]:
    """
    Liveness probe for orchestrators (Kubernetes, Docker).

    Returns 200 if server is running.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(supabase: SupabaseDep) -> dict[str, str]:
    """
    Readiness probe for orchestrators.

    Returns 200 if server can handle requests (dependencies are healthy).
    """
    db_healthy = await supabase.health_check()

    if not db_healthy:
        return {"status": "not ready", "reason": "database unavailable"}

    return {"status": "ready"}
