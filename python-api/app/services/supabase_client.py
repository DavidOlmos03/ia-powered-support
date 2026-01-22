"""
Supabase database client service.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from supabase import Client, create_client
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.exceptions import DatabaseConnectionError, DatabaseError, NotFoundError
from app.core.logging_config import get_logger
from app.models.domain import ClassificationResult, TicketRecord

logger = get_logger(__name__)


class SupabaseService:
    """Service for interacting with Supabase database."""

    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = self._initialize_client()

    def _initialize_client(self) -> Client:
        """Initialize Supabase client with service role key."""
        try:
            client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_service_role_key,
            )
            logger.info("Supabase client initialized successfully")
            return client
        except Exception as e:
            logger.error("Failed to initialize Supabase client", error=str(e))
            raise DatabaseConnectionError(f"Failed to connect to database: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def get_ticket(self, ticket_id: UUID) -> Optional[TicketRecord]:
        """
        Fetch a ticket by ID.

        Args:
            ticket_id: Ticket UUID

        Returns:
            TicketRecord if found, None otherwise

        Raises:
            DatabaseError: If query fails
        """
        try:
            logger.debug("Fetching ticket from database", ticket_id=str(ticket_id))

            response = (
                self.client.table("tickets")
                .select("*")
                .eq("id", str(ticket_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.warning("Ticket not found", ticket_id=str(ticket_id))
                return None

            ticket_data = response.data[0]
            logger.debug("Ticket fetched successfully", ticket_id=str(ticket_id))

            return TicketRecord(**ticket_data)

        except Exception as e:
            logger.error(
                "Failed to fetch ticket",
                ticket_id=str(ticket_id),
                error=str(e),
                exc_info=True,
            )
            raise DatabaseError(f"Failed to fetch ticket: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def start_processing(self, ticket_id: UUID) -> None:
        """
        Mark ticket as processing started.

        Args:
            ticket_id: Ticket UUID

        Raises:
            DatabaseError: If update fails
        """
        try:
            logger.debug("Marking ticket processing started", ticket_id=str(ticket_id))

            self.client.table("tickets").update(
                {"processing_started_at": datetime.utcnow().isoformat()}
            ).eq("id", str(ticket_id)).execute()

            logger.debug("Ticket marked as processing", ticket_id=str(ticket_id))

        except Exception as e:
            logger.error(
                "Failed to mark ticket as processing",
                ticket_id=str(ticket_id),
                error=str(e),
                exc_info=True,
            )
            raise DatabaseError(f"Failed to update ticket: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def complete_processing(
        self, ticket_id: UUID, classification: ClassificationResult
    ) -> TicketRecord:
        """
        Update ticket with classification results.

        Args:
            ticket_id: Ticket UUID
            classification: Classification results

        Returns:
            Updated TicketRecord

        Raises:
            DatabaseError: If update fails
        """
        try:
            logger.info(
                "Updating ticket with classification",
                ticket_id=str(ticket_id),
                category=classification.category.value,
                sentiment=classification.sentiment.value,
            )

            response = (
                self.client.table("tickets")
                .update(
                    {
                        "category": classification.category.value,
                        "sentiment": classification.sentiment.value,
                        "processed": True,
                        "processing_completed_at": datetime.utcnow().isoformat(),
                        "processing_error": None,  # Clear any previous errors
                    }
                )
                .eq("id", str(ticket_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise DatabaseError("No ticket was updated")

            logger.info("Ticket updated successfully", ticket_id=str(ticket_id))

            return TicketRecord(**response.data[0])

        except Exception as e:
            logger.error(
                "Failed to update ticket with classification",
                ticket_id=str(ticket_id),
                error=str(e),
                exc_info=True,
            )
            raise DatabaseError(f"Failed to update ticket: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def record_error(self, ticket_id: UUID, error_message: str) -> None:
        """
        Record processing error for a ticket.

        Args:
            ticket_id: Ticket UUID
            error_message: Error description

        Raises:
            DatabaseError: If update fails
        """
        try:
            logger.warning(
                "Recording processing error",
                ticket_id=str(ticket_id),
                error=error_message,
            )

            self.client.table("tickets").update(
                {
                    "processing_error": error_message,
                    "retry_count": self.client.table("tickets")
                    .select("retry_count")
                    .eq("id", str(ticket_id))
                    .execute()
                    .data[0]["retry_count"]
                    + 1,
                }
            ).eq("id", str(ticket_id)).execute()

            logger.debug("Error recorded for ticket", ticket_id=str(ticket_id))

        except Exception as e:
            logger.error(
                "Failed to record error",
                ticket_id=str(ticket_id),
                error=str(e),
                exc_info=True,
            )
            # Don't raise here - this is a best-effort operation

    async def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            True if database is reachable, False otherwise
        """
        try:
            # Simple query to test connection
            self.client.table("tickets").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
