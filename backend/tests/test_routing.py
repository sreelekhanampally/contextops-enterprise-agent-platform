import pytest

from app.services.llm import MockLLMService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "question,expected",
    [
        ("How many annual leave days do employees receive?", "retrieval"),
        ("Which department has the highest number of open tickets?", "sql"),
        ("Compare our incident policy with current unresolved incidents", "hybrid"),
        ("Create a high-priority incident for a database outage", "action"),
    ],
)
async def test_mock_router(question, expected):
    route = await MockLLMService().route(question)
    assert route.route == expected
