"""
Prompt builder service for LLM classification.
"""

from typing import Any


class PromptBuilderService:
    """Service for constructing LLM prompts."""

    def __init__(self):
        """Initialize prompt builder."""
        self.system_message = self._build_system_message()
        self.few_shot_examples = self._get_few_shot_examples()

    def _build_system_message(self) -> str:
        """Build the system message for chat models."""
        return "You are a support ticket classifier for a Spanish-language customer service system. Always respond with valid JSON only."

    def _get_few_shot_examples(self) -> list[dict[str, str]]:
        """Get few-shot examples for the prompt."""
        return [
            {
                "input": "Mi factura tiene un cargo duplicado este mes",
                "output": '{"category": "Facturación", "sentiment": "Negativo"}',
            },
            {
                "input": "¿Cómo reseteo mi contraseña?",
                "output": '{"category": "Técnico", "sentiment": "Neutral"}',
            },
            {
                "input": "Excelente servicio, gracias por la ayuda",
                "output": '{"category": "Comercial", "sentiment": "Positivo"}',
            },
            {
                "input": "No puedo conectarme desde ayer, muy frustrado",
                "output": '{"category": "Técnico", "sentiment": "Negativo"}',
            },
            {
                "input": "Quiero información sobre el plan premium",
                "output": '{"category": "Comercial", "sentiment": "Neutral"}',
            },
        ]

    def build_classification_prompt(
        self, description: str, include_examples: bool = True
    ) -> str:
        """
        Build the complete classification prompt.

        Args:
            description: Ticket description to classify
            include_examples: Whether to include few-shot examples

        Returns:
            Complete prompt string
        """
        prompt_parts = [
            "You are a support ticket classifier for a Spanish-language customer service system.",
            "",
            "TASK: Analyze the ticket and return ONLY a valid JSON object with category and sentiment.",
            "",
            "CATEGORIES (choose exactly one):",
            '- "Técnico": Technical issues, bugs, errors, connectivity, passwords, system access',
            '- "Facturación": Billing, payments, invoices, charges, refunds, pricing',
            '- "Comercial": Sales, product info, upgrades, features, feedback, general inquiries',
            "",
            "SENTIMENT (choose exactly one):",
            '- "Positivo": Satisfaction, praise, gratitude, enthusiasm',
            '- "Neutral": Questions, factual statements, neutral tone',
            '- "Negativo": Complaints, frustration, anger, dissatisfaction',
            "",
            "RULES:",
            '1. Output ONLY valid JSON: {"category": "X", "sentiment": "Y"}',
            "2. NO explanations, NO markdown, NO extra text",
            "3. Use exact category/sentiment values (case-sensitive)",
            '4. If ambiguous, prefer: category="Técnico", sentiment="Neutral"',
        ]

        if include_examples:
            prompt_parts.extend(
                [
                    "",
                    "EXAMPLES:",
                    "",
                ]
            )
            for example in self.few_shot_examples:
                prompt_parts.append(f'Input: "{example["input"]}"')
                prompt_parts.append(f'Output: {example["output"]}')
                prompt_parts.append("")

        prompt_parts.extend(
            [
                "Now classify this ticket:",
                "",
                f'Input: "{description}"',
                "Output:",
            ]
        )

        return "\n".join(prompt_parts)

    def build_chat_messages(self, description: str) -> list[dict[str, str]]:
        """
        Build messages for chat-based models (OpenAI, Claude).

        Args:
            description: Ticket description to classify

        Returns:
            List of message dictionaries
        """
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": self.build_classification_prompt(description)},
        ]

        return messages
