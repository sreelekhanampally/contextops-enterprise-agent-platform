import pytest

from app.services.llm import MockLLMService
from app.services.validator import GroundingValidator


@pytest.mark.asyncio
async def test_insufficient_context_is_safe_and_grounded():
    validator = GroundingValidator(MockLLMService())
    result = await validator.validate(
        "What is our secret policy?",
        "I do not have enough enterprise evidence to answer that reliably.",
        [],
        None,
    )
    assert result.grounded is True
    assert result.confidence >= 0.8
