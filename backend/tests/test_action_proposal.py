import pytest

from app.services.llm import MockLLMService


@pytest.mark.asyncio
async def test_action_parser_does_not_execute_and_extracts_proposal():
    proposal = await MockLLMService().propose_incident(
        "Create a critical incident for a production database outage assigned to Platform Engineering"
    )
    assert proposal.priority == "CRITICAL"
    assert proposal.team == "Platform Engineering"
    assert "database outage" in proposal.title.lower()


@pytest.mark.asyncio
async def test_action_parser_respects_known_team_and_priority():
    proposal = await MockLLMService().propose_incident(
        "Raise a medium priority incident for a refund backlog assigned to Customer Support"
    )
    assert proposal.priority == "MEDIUM"
    assert proposal.team == "Customer Support"
