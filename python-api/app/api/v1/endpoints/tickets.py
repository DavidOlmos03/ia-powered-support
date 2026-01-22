"""
Ticket processing endpoints.
"""

import time
import uuid
from contextvars import ContextVar

from fastapi import APIRouter, HTTPException, Request, status

from app.core.exceptions import (
    DatabaseError,
    LLMServiceError,
    LLMTimeoutError,
    NotFoundError,
)
from app.core.logging_config import get_logger
from app.dependencies import ApiKeyDep, ClassifierDep, SupabaseDep
from app.models.requests import ProcessTicketRequest
from app.models.responses import ErrorDetail, ErrorResponse, ProcessTicketResponse

router = APIRouter(tags=["tickets"], dependencies=[ApiKeyDep])
logger = get_logger(__name__)

# Context variable for request ID
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


@router.post(
    "/process-ticket",
    response_model=ProcessTicketResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Ticket not found"},
        422: {"model": ErrorResponse, "description": "Business logic error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)
async def process_ticket(
    request: ProcessTicketRequest,
    classifier: ClassifierDep,
    supabase: SupabaseDep,
    http_request: Request,
) -> ProcessTicketResponse:
    """
    Process a support ticket through AI classification.

    This endpoint:
    1. Fetches the ticket from the database
    2. Checks if it's already processed (idempotency)
    3. Classifies it using LLM
    4. Updates the database with results
    5. Returns the classification

    Args:
        request: ProcessTicketRequest with ticket_id and description
        classifier: Injected ClassifierService
        supabase: Injected SupabaseService
        http_request: FastAPI Request object

    Returns:
        ProcessTicketResponse with classification results

    Raises:
        HTTPException: Various error responses based on failure type
    """
    start_time = time.time()

    # Generate request ID for tracking
    req_id = f"req_{uuid.uuid4().hex[:12]}"
    request_id_ctx.set(req_id)

    logger.info(
        "Processing ticket request",
        request_id=req_id,
        ticket_id=str(request.ticket_id),
        description_length=len(request.description),
    )

    try:
        # Step 1: Fetch ticket from database
        ticket = await supabase.get_ticket(request.ticket_id)

        if ticket is None:
            logger.warning(
                "Ticket not found",
                request_id=req_id,
                ticket_id=str(request.ticket_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "TICKET_NOT_FOUND",
                        "message": f"Ticket with ID {request.ticket_id} does not exist",
                        "field": "ticket_id",
                    },
                    "request_id": req_id,
                },
            )

        # Step 2: Check if already processed (idempotency)
        if ticket.processed:
            logger.info(
                "Ticket already processed, returning cached result",
                request_id=req_id,
                ticket_id=str(request.ticket_id),
                category=ticket.category.value if ticket.category else None,
                sentiment=ticket.sentiment.value if ticket.sentiment else None,
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            return ProcessTicketResponse(
                success=True,
                ticket_id=request.ticket_id,
                classification={
                    "category": ticket.category,
                    "sentiment": ticket.sentiment,
                    "confidence_score": None,
                },
                processing_time_ms=processing_time_ms,
                message="Ticket was already processed (cached result)",
            )

        # Step 3: Mark processing started
        await supabase.start_processing(request.ticket_id)

        # Step 4: Classify ticket using LLM
        try:
            classification = await classifier.classify_ticket(request.description)

            logger.info(
                "Ticket classified",
                request_id=req_id,
                ticket_id=str(request.ticket_id),
                category=classification.category.value,
                sentiment=classification.sentiment.value,
            )

        except LLMTimeoutError as e:
            logger.error(
                "LLM timeout error",
                request_id=req_id,
                ticket_id=str(request.ticket_id),
                error=str(e),
            )
            # Record error in database
            await supabase.record_error(request.ticket_id, "LLM request timed out")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "success": False,
                    "error": {
                        "code": "LLM_TIMEOUT",
                        "message": "LLM service timed out. Please try again.",
                        "field": None,
                    },
                    "request_id": req_id,
                },
            ) from e

        except LLMServiceError as e:
            logger.error(
                "LLM service error",
                request_id=req_id,
                ticket_id=str(request.ticket_id),
                error=str(e),
            )
            # Record error in database
            await supabase.record_error(request.ticket_id, str(e))

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": {
                        "code": "LLM_SERVICE_ERROR",
                        "message": "Failed to classify ticket. Please try again later.",
                        "field": None,
                    },
                    "request_id": req_id,
                },
            ) from e

        # Step 5: Update database with results
        try:
            updated_ticket = await supabase.complete_processing(
                request.ticket_id, classification
            )

            logger.info(
                "Ticket updated in database",
                request_id=req_id,
                ticket_id=str(request.ticket_id),
            )

        except DatabaseError as e:
            logger.error(
                "Database error updating ticket",
                request_id=req_id,
                ticket_id=str(request.ticket_id),
                error=str(e),
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "success": False,
                    "error": {
                        "code": "DATABASE_ERROR",
                        "message": "Failed to update ticket in database",
                        "field": None,
                    },
                    "request_id": req_id,
                },
            ) from e

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Ticket processing completed",
            request_id=req_id,
            ticket_id=str(request.ticket_id),
            processing_time_ms=processing_time_ms,
        )

        # Return successful response
        return ProcessTicketResponse(
            success=True,
            ticket_id=request.ticket_id,
            classification=classification,
            processing_time_ms=processing_time_ms,
            message="Ticket processed successfully",
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(
            "Unexpected error processing ticket",
            request_id=req_id,
            ticket_id=str(request.ticket_id),
            error=str(e),
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again.",
                    "field": None,
                },
                "request_id": req_id,
            },
        ) from e
