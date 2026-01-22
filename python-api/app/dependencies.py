"""
Dependency injection providers for FastAPI.
"""

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import settings
from app.services.classifier import ClassifierService
from app.services.supabase_client import SupabaseService

# Global service instances (singletons)
_classifier_service: ClassifierService | None = None
_supabase_service: SupabaseService | None = None


def get_classifier_service() -> ClassifierService:
    """
    Get or create the classifier service singleton.

    Returns:
        ClassifierService instance
    """
    global _classifier_service
    if _classifier_service is None:
        _classifier_service = ClassifierService()
    return _classifier_service


def get_supabase_service() -> SupabaseService:
    """
    Get or create the Supabase service singleton.

    Returns:
        SupabaseService instance
    """
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service


async def verify_api_key(
    x_api_key: Annotated[str, Header(alias="X-API-Key")]
) -> None:
    """
    Verify API key from request header.

    Args:
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: If API key is invalid (401)
    """
    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )


# Type aliases for dependency injection
ClassifierDep = Annotated[ClassifierService, Depends(get_classifier_service)]
SupabaseDep = Annotated[SupabaseService, Depends(get_supabase_service)]
ApiKeyDep = Annotated[None, Depends(verify_api_key)]
