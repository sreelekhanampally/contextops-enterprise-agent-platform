import pytest

from app.services.llm import MockLLMService, ResilientLLMService


class RateLimitedBackend(MockLLMService):
    def __init__(self):
        self.answer_calls = 0

    async def answer(self, question, document_context, sql_context):
        self.answer_calls += 1
        raise RuntimeError("429 quota exceeded; retry_delay=60")


class LocalBackend(MockLLMService):
    def __init__(self):
        self.answer_calls = 0
        self.sql_calls = 0

    async def answer(self, question, document_context, sql_context):
        self.answer_calls += 1
        return "Employees receive 24 working days of paid annual leave."

    async def draft_sql(self, question, schema):
        self.sql_calls += 1
        return await super().draft_sql(question, schema)


@pytest.mark.asyncio
async def test_rate_limited_gemini_fails_over_to_local_backend():
    cloud = RateLimitedBackend()
    local = LocalBackend()
    service = ResilientLLMService(backends=[("gemini", cloud), ("ollama", local)])

    answer = await service.answer(
        "How many annual leave days do employees receive?",
        "Full-time employees receive 24 working days of paid annual leave.",
        "",
    )

    assert "24 working days" in answer
    assert cloud.answer_calls == 1
    assert local.answer_calls == 1

    # Circuit breaker: the next request skips the cloud backend during cooldown.
    await service.answer(
        "How many annual leave days do employees receive?",
        "Full-time employees receive 24 working days of paid annual leave.",
        "",
    )
    assert cloud.answer_calls == 1
    assert local.answer_calls == 2


@pytest.mark.asyncio
async def test_common_sql_intent_does_not_spend_generation_call():
    cloud = RateLimitedBackend()
    local = LocalBackend()
    service = ResilientLLMService(backends=[("gemini", cloud), ("ollama", local)])

    draft = await service.draft_sql(
        "Which department has the highest number of open tickets?",
        "tickets(department text, status text)",
    )

    assert "COUNT" in draft.sql.upper()
    assert "status = 'OPEN'" in draft.sql
    assert local.sql_calls == 0


@pytest.mark.asyncio
async def test_deterministic_validator_rejects_unsupported_number():
    service = MockLLMService()
    result = await service.validate(
        "How many annual leave days?",
        "Employees receive 30 annual leave days.",
        "Employees receive 24 annual leave days.",
    )
    assert result.grounded is False
    assert result.unsupported_claims
