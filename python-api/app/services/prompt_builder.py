"""
Prompt builder service for LLM classification.
"""

from typing import Any


class PromptBuilderService:
    """
    A service dedicated to constructing detailed and effective prompts for the LLM.

    This service encapsulates all the logic related to prompt engineering,
    including defining the role of the AI, specifying the task, providing
    clear definitions for categories and sentiments, and including few-shot
    examples to improve classification accuracy.

    Separating prompt logic here makes it easy to experiment with and refine
    prompts without altering the core classification service.
    """

    def __init__(self) -> None:
        """Initializes the prompt builder service."""
        self.system_message = self._build_system_message()
        self.few_shot_examples = self._get_few_shot_examples()

    def _build_system_message(self) -> str:
        """
        Builds the initial system message for chat-based models.

        This message sets the context for the AI, defining its role as a
        specialized classifier and establishing the primary rule of
        responding only with JSON.

        Returns:
            The system message string.
        """
        return (
            "You are an expert support ticket classifier for a Spanish-language "
            "customer service system. Your sole purpose is to analyze a ticket's "
            "content and return a valid JSON object with its classification. "
            "You must not provide any explanations, apologies, or conversational text."
        )

    def _get_few_shot_examples(self) -> list[dict[str, str]]:
        """
        Provides a list of curated examples for few-shot prompting.

        These examples help the LLM understand the expected input/output format
        and improve its accuracy by showing concrete cases for each category
        and sentiment.

        Returns:
            A list of dictionaries, where each dictionary represents a single
            few-shot example with an "input" and "output" key.
        """
        return [
            {
                "input": "Mi factura tiene un cargo duplicado este mes. ¿Pueden arreglarlo?",
                "output": '{"category": "Facturación", "sentiment": "Negativo"}',
            },
            {
                "input": "¿Cómo puedo resetear mi contraseña? No encuentro la opción.",
                "output": '{"category": "Técnico", "sentiment": "Neutral"}',
            },
            {
                "input": "¡Excelente servicio! Me resolvieron el problema súper rápido. Gracias.",
                "output": '{"category": "Comercial", "sentiment": "Positivo"}',
            },
            {
                "input": "La conexión a internet ha estado intermitente todo el día.",
                "output": '{"category": "Técnico", "sentiment": "Negativo"}',
            },
            {
                "input": "Quisiera más información sobre los planes de fibra óptica.",
                "output": '{"category": "Comercial", "sentiment": "Neutral"}',
            },
        ]

    def build_classification_prompt(self, description: str) -> str:
        """
        Constructs the full, detailed prompt for classifying a ticket description.

        This method assembles the final prompt by combining the task definition,
        category/sentiment rules, few-shot examples, and the specific ticket
        description that needs to be classified.

        Args:
            description: The raw text from the support ticket.

        Returns:
            A complete, formatted prompt string ready to be sent to the LLM.
        """
        # Using a list of strings for efficient joining.
        prompt_parts = [
            "TASK: Analyze the user's support ticket and return ONLY a valid JSON object with 'category' and 'sentiment' fields.",
            "\nDEFINITIONS:",
            "1. CATEGORIES:",
            '   - "Técnico": Technical issues (e.g., bugs, errors, connectivity, passwords, system access).',
            '   - "Facturación": Billing matters (e.g., payments, invoices, charges, refunds, pricing).',
            '   - "Comercial": General inquiries (e.g., sales, product info, upgrades, feedback).',
            "2. SENTIMENTS:",
            '   - "Positivo": User expresses satisfaction, praise, or gratitude.',
            '   - "Neutral": User asks a question, makes a factual statement, or has a neutral tone.',
            '   - "Negativo": User expresses complaints, frustration, anger, or dissatisfaction.',
            "\nRULES:",
            '1. Your response MUST be a single, valid JSON object: {"category": "VALUE", "sentiment": "VALUE"}.',
            "2. DO NOT include explanations, markdown (` ```json `), or any text outside the JSON object.",
            "3. Use the exact, case-sensitive category and sentiment values defined above.",
            '4. If a ticket is ambiguous, use the default classification: {"category": "Técnico", "sentiment": "Neutral"}.',
            "\nEXAMPLES:",
        ]

        # Append few-shot examples for context
        for example in self.few_shot_examples:
            prompt_parts.append(f'\nInput: "{example["input"]}"\nOutput: {example["output"]}')

        # Append the actual ticket to be classified
        prompt_parts.extend(
            [
                "\nTICKET TO CLASSIFY:",
                f'\nInput: "{description}"\nOutput:',
            ]
        )

        return "\n".join(prompt_parts)

    def messages_to_prompt(self, messages: list[Any]) -> str:
        """
        Converts a list of LangChain message objects into a single string prompt.

        Useful for models or providers (like HuggingFace's InferenceClient)
        that expect a single consolidated string instead of a structured list
        of messages.

        Args:
            messages: A list of LangChain `SystemMessage` or `HumanMessage` objects.

        Returns:
            A single formatted string combining all message content.
        """
        return "\n".join(
            [f"{'System: ' if msg.type == 'system' else 'User: '}{msg.content}" for msg in messages]
        )
