"""
API response schemas.
"""

from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .domain import ClassificationResult


class ProcessTicketResponse(BaseModel):
    """Response from ticket processing."""

    success: bool = Field(..., description="Whether processing succeeded")
    ticket_id: UUID = Field(..., description="Processed ticket ID")
    classification: ClassificationResult = Field(
        ..., description="Classification results"
    )
    processing_time_ms: int = Field(
        ..., description="Processing time in milliseconds"
    )
    message: str = Field(..., description="Human-readable message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
                "classification": {
                    "category": "Técnico",
                    "sentiment": "Negativo",
                    "confidence_score": 0.89,
                },
                "processing_time_ms": 1234,
                "message": "Ticket processed successfully",
            }
        }


class ErrorDetail(BaseModel):
    """Error detail information."""

    code: str = Field(..., description="Error code (e.g., VALIDATION_ERROR)")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")


class ErrorResponse(BaseModel):
    """Error response."""

    success: Literal[False] = False
    error: ErrorDetail = Field(..., description="Error details")
    request_id: str = Field(..., description="Unique request identifier for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Description must be at least 10 characters",
                    "field": "description",
                },
                "request_id": "req_abc123xyz",
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "unhealthy"] = Field(
        ..., description="Overall health status"
    )
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    services: dict[str, str] = Field(..., description="Status of dependent services")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-01-22T10:30:00Z",
                "services": {"database": "up", "llm": "up"},
            }
        }
