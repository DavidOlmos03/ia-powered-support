"""
This module contains the API endpoints related to ticket processing.
"""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.exceptions import LLMServiceError, LLMTimeoutError, NotFoundError
from app.core.logging_config import get_logger
from app.dependencies import ApiKeyDep, ClassifierDep, SupabaseDep
from app.models.requests import ProcessTicketRequest
from app.models.responses import ProcessTicketResponse

# All endpoints in this router require a valid API key.
router = APIRouter(tags=["Tickets"], dependencies=[ApiKeyDep])
logger = get_logger(__name__)


@router.post(
    "/process-ticket",
    response_model=ProcessTicketResponse,
    summary="Process and Classify a Support Ticket",
    description="This is the core endpoint for classifying a support ticket. It orchestrates the entire workflow: fetching ticket data, invoking the AI classification service, and updating the database with the result.",
    responses={
        404: {"description": "The requested ticket ID was not found."},
        422: {"description": "The ticket has already been processed (idempotency)."},
        500: {"description": "An internal error occurred during processing."},
        503: {"description": "A downstream service (like the LLM or database) is unavailable."},
    },
)
async def process_ticket(
    request: ProcessTicketRequest,
    classifier: ClassifierDep,
    supabase: SupabaseDep,
    http_request: Request,
) -> ProcessTicketResponse:
    """
    Processes a single support ticket by classifying its content.

    This endpoint is designed to be idempotent. If a ticket has already been
    processed, it will return the existing classification result without
-   re-running the AI model.

    Workflow:
    1.  Fetches the ticket from Supabase.
    2.  Checks if the ticket has a `processed` flag set to `True`.
    3.  If not processed, it calls the `ClassifierService` to get the category
        and sentiment.
    4.  Updates the ticket record in the database with the classification result.
    5.  Returns a detailed response including the classification and processing time.

    Args:
        request: The request body containing the `ticket_id` and `description`.
        classifier: The dependency-injected `ClassifierService`.
        supabase: The dependency-injected `SupabaseService`.
        http_request: The raw FastAPI request object for logging and context.

    Returns:
        A `ProcessTicketResponse` with the outcome of the classification.

    Raises:
        HTTPException:
            - 404: If the ticket ID does not exist.
            - 422: If the ticket was already processed.
            - 503: If the database or LLM service fails.
            - 500: For any other unexpected errors.
    """
    start_time = time.time()
    request_id = http_request.state.request_id
    ticket_id = request.ticket_id

    logger.info("Starting ticket processing", ticket_id=ticket_id, request_id=request_id)

    try:
        # Step 1: Fetch the ticket from the database.
        ticket = await supabase.get_ticket(ticket_id)

        # Step 2: Handle idempotency - if already processed, return the stored result.
        if ticket.processed and ticket.category and ticket.sentiment:
            logger.info("Ticket was already processed, returning cached result.", ticket_id=ticket_id)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "This ticket has already been processed.",
                    "classification": {
                        "category": ticket.category.value,
                        "sentiment": ticket.sentiment.value,
                    },
                },
            )

        # Step 3: Call the classifier service to get the AI-powered classification.
        classification_result = await classifier.classify_ticket(request.description)

        # Step 4: Update the database with the new classification.
        await supabase.update_ticket_classification(ticket_id, classification_result)

        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.info("Ticket processed successfully", ticket_id=ticket_id, duration_ms=processing_time_ms)

        # Step 5: Return the successful response.
        return ProcessTicketResponse(
            success=True,
            ticket_id=ticket_id,
            classification=classification_result,
            processing_time_ms=processing_time_ms,
            message="Ticket classified and updated successfully.",
        )

    except NotFoundError as e:
        logger.warning("Ticket not found during processing.", ticket_id=ticket_id, error=e.message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e

    except (LLMTimeoutError, LLMServiceError) as e:
        error_message = f"LLM service failed: {e}"
        logger.error(error_message, ticket_id=ticket_id, exc_info=True)
        await supabase.record_processing_error(ticket_id, error_message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Classification service is currently unavailable. {e}"
        ) from e

    except Exception as e:
        # Catch-all for any other unexpected errors.
        logger.error("An unexpected error occurred during ticket processing.", ticket_id=ticket_id, exc_info=True)
        await supabase.record_processing_error(ticket_id, "An unexpected internal error occurred.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred.") from e
