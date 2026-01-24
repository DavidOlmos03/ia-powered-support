"""
Supabase database client service.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from supabase import Client, create_client
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
import httpx

from app.config import settings
from app.core.exceptions import DatabaseConnectionError, DatabaseError, NotFoundError
from app.core.logging_config import get_logger
from app.models.domain import ClassificationResult, TicketRecord

logger = get_logger(__name__)


class SupabaseService:
    """
    A service for interacting with the Supabase database.

    This class abstracts all database operations, providing a clean and
    centralized interface for the rest of the application. It handles the
    initialization of the Supabase client and includes robust retry logic
    for all database calls to ensure resilience against transient network issues.
    """

    def __init__(self) -> None:
        """
        Initializes the SupabaseService and its underlying client.
        """
        self.client: Client = self._initialize_client()

    def _initialize_client(self) -> Client:
        """
        Creates and configures the Supabase client.

        Uses the connection details from the application settings to establish
        a connection to the Supabase project.

        Returns:
            An initialized `supabase.Client` instance.

        Raises:
            DatabaseConnectionError: If the client fails to initialize,
                                     indicating a configuration or connectivity problem.
        """
        try:
            client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_service_role_key,
            )
            logger.info("Supabase client initialized successfully.")
            return client
        except Exception as e:
            logger.error("Failed to initialize Supabase client.", error=str(e), exc_info=True)
            raise DatabaseConnectionError(f"Could not connect to Supabase: {e}") from e

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def get_ticket(self, ticket_id: UUID) -> TicketRecord:
        """
        Fetches a single support ticket from the database by its unique ID.

        Args:
            ticket_id: The UUID of the ticket to retrieve.

        Returns:
            A `TicketRecord` object representing the fetched ticket.

        Raises:
            NotFoundError: If no ticket with the specified ID is found.
            DatabaseError: If any other database-related error occurs.
        """
        logger.debug("Fetching ticket from database", ticket_id=ticket_id)
        try:
            response = self.client.table("tickets").select("*").eq("id", str(ticket_id)).single().execute()

            if not response.data:
                raise NotFoundError(f"Ticket with ID '{ticket_id}' not found.")

            return TicketRecord(**response.data)
        except PostgrestAPIError as e:
            if e.code == "PGRST116":  # "single() row not found"
                raise NotFoundError(f"Ticket with ID '{ticket_id}' not found.") from e
            logger.error("Database error fetching ticket", ticket_id=ticket_id, error=e.message)
            raise DatabaseError(f"Could not fetch ticket: {e.message}") from e
        except Exception as e:
            logger.error("Unexpected error fetching ticket", ticket_id=ticket_id, error=e, exc_info=True)
            raise DatabaseError(f"An unexpected error occurred: {e}") from e

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def update_ticket_classification(
        self, ticket_id: UUID, classification: ClassificationResult
    ) -> TicketRecord:
        """
        Updates a ticket with the results of an AI classification.

        This method sets the ticket's category, sentiment, and marks it as
        processed. It also clears any previous error messages related to
        processing.

        Args:
            ticket_id: The UUID of the ticket to update.
            classification: The `ClassificationResult` object containing the
                            new category and sentiment.

        Returns:
            The updated `TicketRecord` object.

        Raises:
            NotFoundError: If the ticket to update is not found.
            DatabaseError: If the update operation fails for any other reason.
        """
        logger.info("Updating ticket with classification", ticket_id=ticket_id, category=classification.category.value)
        try:
            update_data = {
                "category": classification.category.value,
                "sentiment": classification.sentiment.value,
                "processed": True,
                "processing_completed_at": datetime.utcnow().isoformat(),
                "processing_error": None,  # Clear any previous errors
            }
            response = self.client.table("tickets").update(update_data).eq("id", str(ticket_id)).single().execute()

            if not response.data:
                raise NotFoundError(f"Could not update ticket with ID '{ticket_id}' as it was not found.")

            logger.info("Ticket updated successfully", ticket_id=ticket_id)
            return TicketRecord(**response.data)
        except PostgrestAPIError as e:
            if e.code == "PGRST116":
                raise NotFoundError(f"Could not update ticket with ID '{ticket_id}' as it was not found.") from e
            logger.error("Database error updating ticket", ticket_id=ticket_id, error=e.message)
            raise DatabaseError(f"Could not update ticket: {e.message}") from e
        except Exception as e:
            logger.error("Unexpected error updating ticket", ticket_id=ticket_id, error=e, exc_info=True)
            raise DatabaseError(f"An unexpected error occurred during update: {e}") from e

    @retry(
        stop=stop_after_attempt(2), # Fewer retries for error logging
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    )
    async def record_processing_error(self, ticket_id: UUID, error_message: str) -> None:
        """
        Records a processing error for a specific ticket in the database.

        This is a best-effort operation. It logs the error message and increments
        a retry counter. Failures in this method are logged but do not raise
        exceptions, to prevent the main processing flow from failing if error
        logging itself has an issue.

        Args:
            ticket_id: The UUID of the ticket that failed to process.
            error_message: A descriptive message of the error that occurred.
        """
        logger.warning("Recording processing error for ticket", ticket_id=ticket_id, error=error_message)
        try:
            # Note: This is not an atomic operation. For high-concurrency scenarios,
            # a database function (RPC) would be more appropriate.
            self.client.table("tickets").update(
                {
                    "processing_error": error_message,
                    "retry_count": self.client.rpc("increment_retry_count", {"ticket_id_param": str(ticket_id)}).execute().data
                }
            ).eq("id", str(ticket_id)).execute()
        except Exception as e:
            # Log the failure to record the error, but do not re-raise.
            # This prevents a failure in error-logging from crashing the worker.
            logger.error(
                "Failed to record processing error in database.",
                ticket_id=ticket_id,
                original_error=error_message,
                logging_error=str(e),
                exc_info=True,
            )

    async def health_check(self) -> bool:
        """
        Performs a simple health check on the database.

        This method attempts to execute a lightweight query to verify that the
        database is reachable and responsive.

        Returns:
            `True` if the database connection is healthy, `False` otherwise.
        """
        try:
            # A simple, fast query to check if the database is responsive.
            self.client.table("tickets").select("id").limit(1).execute()
            logger.debug("Database health check successful.")
            return True
        except Exception as e:
            logger.error("Database health check failed.", error=str(e), exc_info=True)
            return False
