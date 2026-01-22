#!/usr/bin/env python
"""Test script to debug classifier issues."""

import asyncio
import sys
from app.services.classifier import ClassifierService
from app.core.logging_config import get_logger

logger = get_logger(__name__)

async def test_classifier():
    """Test the classifier service."""
    try:
        logger.info("Initializing classifier service...")
        classifier = ClassifierService()

        logger.info("Classifier initialized successfully")

        description = "Mi conexión a internet no funciona desde hace 3 días"
        logger.info(f"Testing classification with: {description}")

        result = await classifier.classify_ticket(description)

        logger.info(
            "Classification successful",
            category=result.category.value,
            sentiment=result.sentiment.value,
            confidence=result.confidence_score,
        )

        print(f"\n✅ SUCCESS!")
        print(f"Category: {result.category.value}")
        print(f"Sentiment: {result.sentiment.value}")
        print(f"Confidence: {result.confidence_score}")

        return True

    except Exception as e:
        logger.error("Classification failed", error=str(e), exc_info=True)
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_classifier())
    sys.exit(0 if success else 1)
