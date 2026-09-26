import pytest

from app.agents.graph import ContextOpsAgentGraph, GraphDependencies
from app.schemas import RetrievedChunk, RouteDecision, ValidationResult


class FakeLLM:
    async def route(self, question):
        return RouteDecision(route="retrieval", rationale="Policy question")

    async def answer(self, question, document_context, sql_context):
        assert "24 working days" in document_context
        assert not sql_context
        return "Employees receive 24 working days of annual leave."

    async def repair(self, question, answer, evidence, notes):
        raise AssertionError("repair should not run for grounded answer")


class FakeRetrieval:
    async def retrieve(self, session, question):
        return [
            RetrievedChunk(
                chunk_id="chunk-1",
                source="hr_policy.md",
                content="Full-time employees receive 24 working days of paid annual leave.",
                score=0.91,
            )
        ]


class FakeSQL:
    async def run(self, session, question):
        raise AssertionError("SQL agent should not run on retrieval route")


class FakeActions:
    async def propose(self, session, question):
        raise AssertionError("Action agent should not run on retrieval route")


class FakeValidator:
    async def validate(self, question, answer, documents, sql_result):
        return ValidationResult(
            grounded=True,
            confidence=0.98,
            notes="Answer is supported by retrieved policy evidence.",
        )

    @staticmethod
    def evidence_text(documents, sql_result):
        return "\n".join(doc.content for doc in documents)


@pytest.mark.asyncio
async def test_retrieval_route_runs_expected_graph_nodes():
    graph = ContextOpsAgentGraph(
        GraphDependencies(
            llm=FakeLLM(),
            retrieval=FakeRetrieval(),
            sql_agent=FakeSQL(),
            actions=FakeActions(),
            validator=FakeValidator(),
        )
    )

    response = await graph.run("How many annual leave days do employees receive?", object())

    assert response.route == "retrieval"
    assert response.validation and response.validation.grounded is True
    assert response.answer.startswith("Employees receive 24")
    assert response.citations[0].source == "hr_policy.md"
    assert [event.node for event in response.trace] == [
        "supervisor",
        "retrieval_agent",
        "reasoning_agent",
        "validator_agent",
    ]
