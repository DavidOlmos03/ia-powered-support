"""
This module provides endpoints for monitoring the health of the API.

It includes a comprehensive health check, a liveness probe, and a readiness
probe, which are standard patterns for services running in orchestrated
environments like Kubernetes.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Response, status

from app.config import settings
from app.dependencies import SupabaseDep
from app.models.responses import HealthResponse

# Create an API router for health check endpoints
router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Comprehensive Health Check",
    description="Provides a detailed health status of the API and its critical dependencies, such as the database and the LLM service.",
)
async def health_check(supabase: SupabaseDep) -> HealthResponse:
    """
    Performs a comprehensive health check of the API and its dependencies.

    This endpoint is designed for monitoring systems to get a detailed overview
    of the service's operational status.

    Args:
        supabase: Dependency-injected Supabase service client.

    Returns:
        A `HealthResponse` object detailing the status of each major component.
    """
    # Check the status of critical downstream services
    db_healthy = await supabase.health_check()
    llm_configured = bool(settings.openai_api_key)  # Simple check if the key is set

    # Determine overall health
    is_healthy = db_healthy and llm_configured
    overall_status = "healthy" if is_healthy else "unhealthy"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services={
            "database": "up" if db_healthy else "down",
            "llm": "configured" if llm_configured else "unconfigured",
        },
    )


@router.get(
    "/health/live",
    summary="Liveness Probe",
    description="A simple endpoint to verify that the API process is running. Responds with a 200 OK if the server is alive.",
)
async def liveness_probe() -> dict[str, str]:
    """
    Checks if the API server process is running.

    This is a lightweight check used by orchestrators (like Kubernetes) to
    determine if the container needs to be restarted. It does not check
    dependencies.

    Returns:
        A dictionary with a simple "alive" status.
    """
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="Readiness Probe",
    description="Verifies that the API is ready to accept traffic by checking its critical dependencies. Responds with 200 OK if ready, or 503 Service Unavailable otherwise.",
)
async def readiness_probe(supabase: SupabaseDep, response: Response) -> dict[str, str]:
    """
    Checks if the API is ready to handle incoming requests.

    This probe is used by orchestrators to determine whether to route traffic
    to this instance. It checks critical dependencies like the database connection.

    Args:
        supabase: Dependency-injected Supabase service client.
        response: The FastAPI response object, used to set the status code.

    Returns:
        A dictionary indicating the readiness status.
    """
    db_healthy = await supabase.health_check()

    if db_healthy:
        return {"status": "ready"}
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready", "details": "Database connection is unhealthy."}
