"""
API v1 routes aggregator.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, tickets

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router)
api_router.include_router(tickets.router, prefix="/api/v1")
