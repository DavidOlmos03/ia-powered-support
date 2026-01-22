"""
LLM-based ticket classification service.
"""

import json
from typing import Any

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.core.exceptions import LLMParseError, LLMServiceError, LLMTimeoutError
from app.core.logging_config import get_logger
from app.models.domain import ClassificationResult, TicketCategory, TicketSentiment
from app.services.prompt_builder import PromptBuilderService

logger = get_logger(__name__)


class ClassifierService:
    """Service for classifying tickets using LLM."""

    def __init__(self):
        """Initialize classifier service."""
        self.prompt_builder = PromptBuilderService()
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> Any:
        """Initialize the LLM based on configuration."""
        if settings.llm_provider == "openai":
            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                request_timeout=settings.llm_timeout,
                api_key=settings.openai_api_key,
            )
        elif settings.llm_provider == "anthropic":
            # For future implementation
            raise NotImplementedError("Anthropic provider not yet implemented")
        elif settings.llm_provider == "huggingface":
            # For future implementation
            raise NotImplementedError("HuggingFace provider not yet implemented")
        else:
            raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=True,
    )
    async def _call_llm_with_retry(self, messages: list[Any]) -> str:
        """
        Call LLM with retry logic.

        Args:
            messages: List of chat messages

        Returns:
            LLM response text

        Raises:
            LLMTimeoutError: If request times out
            LLMServiceError: If LLM service fails
        """
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except TimeoutError as e:
            logger.error("LLM request timed out", error=str(e))
            raise LLMTimeoutError("LLM request timed out") from e
        except Exception as e:
            logger.error("LLM service error", error=str(e), exc_info=True)
            raise LLMServiceError(f"LLM service failed: {str(e)}") from e

    def _parse_llm_response(self, response: str) -> ClassificationResult:
        """
        Parse LLM response into ClassificationResult.

        Args:
            response: Raw LLM response

        Returns:
            ClassificationResult

        Raises:
            LLMParseError: If response cannot be parsed
        """
        try:
            # Remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # Extract content between code blocks
                parts = cleaned.split("```")
                if len(parts) >= 2:
                    cleaned = parts[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]

            cleaned = cleaned.strip()

            # Parse JSON
            data = json.loads(cleaned)

            # Validate required fields
            if "category" not in data or "sentiment" not in data:
                logger.warning(
                    "LLM response missing required fields",
                    response=response,
                    parsed_data=data,
                )
                raise LLMParseError("Missing required fields in LLM response")

            # Validate enum values
            try:
                category = TicketCategory(data["category"])
            except ValueError:
                logger.warning(
                    "Invalid category in LLM response",
                    category=data["category"],
                    valid_categories=[c.value for c in TicketCategory],
                )
                category = TicketCategory.TECNICO  # Default fallback

            try:
                sentiment = TicketSentiment(data["sentiment"])
            except ValueError:
                logger.warning(
                    "Invalid sentiment in LLM response",
                    sentiment=data["sentiment"],
                    valid_sentiments=[s.value for s in TicketSentiment],
                )
                sentiment = TicketSentiment.NEUTRAL  # Default fallback

            confidence_score = data.get("confidence_score")

            return ClassificationResult(
                category=category,
                sentiment=sentiment,
                confidence_score=confidence_score,
            )

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse LLM response as JSON",
                response=response,
                error=str(e),
            )
            # Return default fallback
            logger.info("Using default fallback classification")
            return ClassificationResult(
                category=TicketCategory.TECNICO,
                sentiment=TicketSentiment.NEUTRAL,
                confidence_score=None,
            )
        except Exception as e:
            logger.error(
                "Unexpected error parsing LLM response",
                response=response,
                error=str(e),
                exc_info=True,
            )
            raise LLMParseError(f"Failed to parse LLM response: {str(e)}") from e

    async def classify_ticket(
        self, description: str, max_retries: int = 3, timeout_seconds: float = 10.0
    ) -> ClassificationResult:
        """
        Classify a ticket using LLM.

        Args:
            description: Ticket text content
            max_retries: Number of retry attempts (currently uses global config)
            timeout_seconds: Request timeout (currently uses global config)

        Returns:
            ClassificationResult with category and sentiment

        Raises:
            LLMServiceError: If classification fails after retries
            LLMTimeoutError: If request exceeds timeout
        """
        logger.info("Starting ticket classification", description_length=len(description))

        try:
            # Build messages for chat model
            messages = [
                SystemMessage(content=self.prompt_builder.system_message),
                HumanMessage(
                    content=self.prompt_builder.build_classification_prompt(description)
                ),
            ]

            # Call LLM with retry logic
            response = await self._call_llm_with_retry(messages)

            logger.debug("LLM response received", response=response)

            # Parse response
            result = self._parse_llm_response(response)

            logger.info(
                "Ticket classified successfully",
                category=result.category.value,
                sentiment=result.sentiment.value,
                confidence=result.confidence_score,
            )

            return result

        except (LLMTimeoutError, LLMServiceError):
            # Re-raise known LLM errors
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during classification",
                error=str(e),
                exc_info=True,
            )
            raise LLMServiceError(f"Classification failed: {str(e)}") from e
