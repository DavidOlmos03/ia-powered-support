"""
API request schemas.
"""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProcessTicketRequest(BaseModel):
    """Request to process a support ticket."""

    ticket_id: UUID = Field(..., description="UUID of the ticket to process")
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Ticket content text (10-5000 characters)",
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Sanitize and validate description."""
        # Remove excessive whitespace
        cleaned = " ".join(v.split())

        if len(cleaned) < 10:
            raise ValueError("Description must be at least 10 characters after cleaning")

        return cleaned

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
                "description": "Mi conexión a internet no funciona desde hace 3 días",
            }
        }
