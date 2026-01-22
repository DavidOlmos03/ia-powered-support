"""
Domain models and enums.
These represent the core business entities.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    """Ticket category classification."""

    TECNICO = "Técnico"
    FACTURACION = "Facturación"
    COMERCIAL = "Comercial"


class TicketSentiment(str, Enum):
    """Ticket sentiment analysis."""

    POSITIVO = "Positivo"
    NEUTRAL = "Neutral"
    NEGATIVO = "Negativo"


class ClassificationResult(BaseModel):
    """Result of ticket classification."""

    category: TicketCategory = Field(..., description="Classified category")
    sentiment: TicketSentiment = Field(..., description="Detected sentiment")
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Model confidence score (0-1), if available",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "category": "Técnico",
                "sentiment": "Negativo",
                "confidence_score": 0.89,
            }
        }


class TicketRecord(BaseModel):
    """Database ticket record."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    description: str
    category: Optional[TicketCategory]
    sentiment: Optional[TicketSentiment]
    processed: bool
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_error: Optional[str]
    retry_count: int

    class Config:
        from_attributes = True
