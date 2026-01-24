"""
LLM-based ticket classification service.
"""

import json
from typing import Any
import httpx

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from huggingface_hub import InferenceClient
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
    """
    A service for classifying support tickets using a Large Language Model (LLM).

    This service handles the entire classification workflow, including:
    - Initializing the appropriate LLM based on application settings.
    - Building a structured prompt for the LLM.
    - Calling the LLM API with robust retry and error handling.
    - Parsing and validating the LLM's response.
    - Returning a structured classification result.

    The service is designed to be extensible, allowing for different LLM providers
    (e.g., OpenAI, HuggingFace, Ollama) to be used interchangeably.
    """

    def __init__(self) -> None:
        """
        Initializes the ClassifierService.

        This sets up the prompt builder and initializes the LLM client based on
        the configuration specified in the application settings.
        """
        self.prompt_builder = PromptBuilderService()
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> Any:
        """
        Initializes and returns the LLM client based on application settings.

        This method acts as a factory, creating a client for the configured
        LLM provider (e.g., OpenAI, HuggingFace, Ollama). It reads the
        `llm_provider` from the settings and returns the corresponding
        initialized client.

        Returns:
            An instance of the LLM client (e.g., `ChatOpenAI`, `InferenceClient`).

        Raises:
            NotImplementedError: If the configured provider is not yet supported.
            ValueError: If the `llm_provider` setting is unknown.
        """
        provider = settings.llm_provider
        logger.info("Initializing LLM", provider=provider, model=settings.llm_model)

        if provider == "openai":
            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                request_timeout=settings.llm_timeout,
                api_key=settings.openai_api_key,
            )
        elif provider == "huggingface":
            return InferenceClient(token=settings.hf_api_token)
        elif provider == "ollama":
            return httpx.AsyncClient(
                base_url=settings.ollama_base_url, timeout=settings.llm_timeout
            )
        elif provider == "anthropic":
            raise NotImplementedError("Anthropic provider not yet implemented.")
        else:
            raise ValueError(f"Unknown LLM provider configured: '{provider}'")

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    async def _call_llm_with_retry(self, messages: list[Any]) -> str:
        """
        Calls the configured LLM with a list of messages, with retry logic.

        This method sends the request to the appropriate LLM provider API. It is
        decorated with `tenacity.retry` to automatically handle transient network
        issues like timeouts or connection errors by retrying the call with
        exponential backoff.

        Args:
            messages: A list of message objects compatible with the LLM provider
                      (e.g., `SystemMessage`, `HumanMessage` for LangChain).

        Returns:
            The raw string content of the LLM's response.

        Raises:
            LLMTimeoutError: If the request to the LLM times out after all retries.
            LLMServiceError: For any other non-transient API error from the LLM.
        """
        provider = settings.llm_provider
        logger.debug("Calling LLM provider", provider=provider)

        try:
            if provider == "openai":
                response = await self.llm.ainvoke(messages)
                return response.content
            elif provider == "huggingface":
                prompt = self.prompt_builder.messages_to_prompt(messages)
                response = self.llm.text_generation(
                    prompt,
                    model=settings.llm_model,
                    max_new_tokens=settings.llm_max_tokens,
                    temperature=settings.llm_temperature,
                )
                return response
            elif provider == "ollama":
                ollama_messages = [
                    {"role": "system" if isinstance(msg, SystemMessage) else "user", "content": msg.content}
                    for msg in messages
                ]
                response = await self.llm.post(
                    "/api/chat",
                    json={
                        "model": settings.llm_model,
                        "messages": ollama_messages,
                        "stream": False,
                        "options": {
                            "temperature": settings.llm_temperature,
                            "num_predict": settings.llm_max_tokens,
                        },
                    },
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except httpx.TimeoutException as e:
            logger.error("LLM request timed out", provider=provider, error=e)
            raise LLMTimeoutError(f"Request to {provider} timed out.") from e
        except Exception as e:
            logger.error("LLM service error", provider=provider, error=e, exc_info=True)
            raise LLMServiceError(f"An error occurred with the {provider} API: {e}") from e

        return ""  # Should not be reached

    def _parse_llm_response(self, response_text: str) -> ClassificationResult:
        """
        Parses the raw JSON string from the LLM into a ClassificationResult object.

        This method is responsible for cleaning the LLM's output, which may include
        markdown code blocks, and then parsing it as JSON. It performs validation
        to ensure the required fields (`category`, `sentiment`) are present and
        that their values are valid enum members.

        If parsing or validation fails, it logs a warning and falls back to a
        default classification (`Técnico`, `Neutral`) to ensure the system
        remains resilient.

        Args:
            response_text: The raw string response from the LLM.

        Returns:
            A `ClassificationResult` object containing the parsed category,
            sentiment, and confidence score.

        Raises:
            LLMParseError: If an unexpected error occurs during parsing, though
                           most common errors are handled gracefully with a fallback.
        """
        logger.debug("Parsing LLM response", response_text=response_text)
        try:
            # Clean the response by removing markdown and stripping whitespace
            cleaned_text = response_text.strip().removeprefix("```json").removesuffix("```").strip()

            data = json.loads(cleaned_text)

            if "category" not in data or "sentiment" not in data:
                logger.warning(
                    "LLM response missing required fields, using fallback.",
                    response_data=data,
                )
                return self._default_classification()

            # Safely create enums with a fallback to default values
            category = self._get_enum_member(TicketCategory, data["category"], TicketCategory.TECNICO)
            sentiment = self._get_enum_member(TicketSentiment, data["sentiment"], TicketSentiment.NEUTRAL)

            return ClassificationResult(
                category=category,
                sentiment=sentiment,
                confidence_score=data.get("confidence_score"),
            )
        except json.JSONDecodeError:
            logger.warning(
                "Failed to decode JSON from LLM response, using fallback.",
                response_text=response_text,
            )
            return self._default_classification()
        except Exception as e:
            logger.error("Unexpected error parsing LLM response", error=e, exc_info=True)
            raise LLMParseError(f"An unexpected error occurred while parsing: {e}") from e

    async def classify_ticket(self, description: str) -> ClassificationResult:
        """
        Classifies a given support ticket description.

        This is the main public method of the service. It orchestrates the
        entire classification process:
        1. Builds the system and user prompts.
        2. Calls the LLM with retry logic.
        3. Parses the response.
        4. Returns the final classification result.

        Args:
            description: The text content of the support ticket to be classified.

        Returns:
            A `ClassificationResult` object with the ticket's category and sentiment.

        Raises:
            LLMServiceError: If the classification fails due to persistent API errors.
            LLMTimeoutError: If the API request times out.
        """
        logger.info("Classifying ticket", description_length=len(description))

        try:
            messages = [
                SystemMessage(content=self.prompt_builder.system_message),
                HumanMessage(content=self.prompt_builder.build_classification_prompt(description)),
            ]

            raw_response = await self._call_llm_with_retry(messages)
            result = self._parse_llm_response(raw_response)

            logger.info(
                "Ticket classified successfully",
                category=result.category.value,
                sentiment=result.sentiment.value,
                confidence=result.confidence_score,
            )
            return result
        except (LLMTimeoutError, LLMServiceError):
            logger.error("Classification failed due to LLM error.")
            raise  # Re-raise the original, specific exception
        except Exception as e:
            logger.error("An unexpected error occurred during classification", error=e, exc_info=True)
            raise LLMServiceError(f"An unexpected error occurred: {e}") from e

    def _default_classification(self) -> ClassificationResult:
        """Returns a default classification result as a fallback."""
        return ClassificationResult(
            category=TicketCategory.TECNICO,
            sentiment=TicketSentiment.NEUTRAL,
        )

    def _get_enum_member(self, enum_class, value, default):
        """Safely gets an enum member, falling back to a default if invalid."""
        try:
            return enum_class(value)
        except ValueError:
            logger.warning(
                "Invalid enum value received, using default.",
                invalid_value=value,
                enum_class=enum_class.__name__,
                default_value=default.value,
            )
            return default
