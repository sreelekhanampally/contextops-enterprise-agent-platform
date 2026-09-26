from __future__ import annotations

import json
from dataclasses import dataclass

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState
from app.schemas import Citation, ChatResponse, TraceEvent, ValidationResult
from app.services.actions import ActionService
from app.services.llm import BaseLLMService
from app.services.retrieval import RetrievalService
from app.services.sql_agent import SQLAgentService
from app.services.validator import GroundingValidator


@dataclass
class GraphDependencies:
    llm: BaseLLMService
    retrieval: RetrievalService
    sql_agent: SQLAgentService
    actions: ActionService
    validator: GroundingValidator


class ContextOpsAgentGraph:
    def __init__(self, deps: GraphDependencies):
        self.deps = deps
        self.graph = self._build().compile()

    @staticmethod
    def _append_trace(state: AgentState, node: str, detail: str) -> list[TraceEvent]:
        return [*(state.get("trace") or []), TraceEvent(node=node, detail=detail)]

    def _build(self):
        builder = StateGraph(AgentState)
        builder.add_node("supervisor", self._supervisor)
        builder.add_node("retrieval", self._retrieval)
        builder.add_node("hybrid_retrieval", self._retrieval)
        builder.add_node("sql", self._sql)
        builder.add_node("hybrid_sql", self._sql)
        builder.add_node("reasoning", self._reasoning)
        builder.add_node("action", self._action)
        builder.add_node("validator", self._validator)
        builder.add_node("repair", self._repair)

        builder.add_edge(START, "supervisor")
        builder.add_conditional_edges(
            "supervisor",
            self._route_after_supervisor,
            {
                "retrieval": "retrieval",
                "sql": "sql",
                "hybrid": "hybrid_retrieval",
                "reasoning": "reasoning",
                "action": "action",
            },
        )
        builder.add_edge("retrieval", "reasoning")
        builder.add_edge("sql", "reasoning")
        builder.add_edge("hybrid_retrieval", "hybrid_sql")
        builder.add_edge("hybrid_sql", "reasoning")
        builder.add_edge("reasoning", "validator")
        builder.add_edge("action", "validator")
        builder.add_conditional_edges(
            "validator",
            self._route_after_validator,
            {"repair": "repair", "end": END},
        )
        builder.add_edge("repair", "validator")
        return builder

    async def _supervisor(self, state: AgentState, config):
        decision = await self.deps.llm.route(state["question"])
        return {
            "route_decision": decision,
            "trace": self._append_trace(
                state,
                "supervisor",
                f"Route={decision.route}. {decision.rationale}",
            ),
            "validation_attempts": state.get("validation_attempts", 0),
        }

    @staticmethod
    def _route_after_supervisor(state: AgentState) -> str:
        return state["route_decision"].route

    async def _retrieval(self, state: AgentState, config):
        session: AsyncSession = config["configurable"]["session"]
        docs = await self.deps.retrieval.retrieve(session, state["question"])
        return {
            "documents": docs,
            "trace": self._append_trace(
                state,
                "retrieval_agent",
                f"Retrieved {len(docs)} evidence chunks from pgvector.",
            ),
        }

    async def _sql(self, state: AgentState, config):
        session: AsyncSession = config["configurable"]["session"]
        result = await self.deps.sql_agent.run(session, state["question"])
        return {
            "sql_result": result,
            "trace": self._append_trace(
                state,
                "sql_agent",
                f"Executed validated read-only SQL and returned {len(result.rows)} row(s).",
            ),
        }

    async def _reasoning(self, state: AgentState, config):
        docs = state.get("documents") or []
        sql_result = state.get("sql_result")
        doc_context = "\n\n".join(
            f"SOURCE: {doc.source}\n{doc.content}" for doc in docs
        )
        sql_context = ""
        if sql_result:
            sql_context = (
                f"QUERY: {sql_result.sql}\n"
                f"RESULT: {json.dumps(sql_result.rows, default=str)}"
            )
        answer = await self.deps.llm.answer(
            state["question"],
            doc_context,
            sql_context,
        )
        return {
            "answer": answer,
            "trace": self._append_trace(
                state,
                "reasoning_agent",
                "Synthesized an answer from the available evidence.",
            ),
        }

    async def _action(self, state: AgentState, config):
        session: AsyncSession = config["configurable"]["session"]
        pending = await self.deps.actions.propose(session, state["question"])
        answer = (
            "I prepared an incident action but did not execute it. "
            "Review the proposed fields and choose Approve or Reject. "
            "The database write only happens after explicit approval."
        )
        return {
            "pending_action": pending,
            "answer": answer,
            "trace": self._append_trace(
                state,
                "action_agent",
                "Created a pending incident proposal; no operational write executed.",
            ),
        }

    async def _validator(self, state: AgentState, config):
        route = state["route_decision"].route
        if route == "action":
            validation = ValidationResult(
                grounded=True,
                confidence=1.0,
                notes="Action is a proposal only and explicitly requires human approval.",
                unsupported_claims=[],
            )
        elif route == "reasoning":
            validation = ValidationResult(
                grounded=True,
                confidence=0.80,
                notes="General reasoning route; no enterprise factual evidence was required.",
                unsupported_claims=[],
            )
        else:
            validation = await self.deps.validator.validate(
                state["question"],
                state.get("answer", ""),
                state.get("documents") or [],
                state.get("sql_result"),
            )

        attempts = state.get("validation_attempts", 0)
        return {
            "validation": validation,
            "trace": self._append_trace(
                state,
                "validator_agent",
                (
                    f"Grounded={validation.grounded}; "
                    f"confidence={validation.confidence:.2f}. {validation.notes}"
                ),
            ),
            "validation_attempts": attempts,
        }

    @staticmethod
    def _route_after_validator(state: AgentState) -> str:
        validation = state.get("validation")
        if (
            validation
            and not validation.grounded
            and state.get("validation_attempts", 0) < 1
        ):
            return "repair"
        return "end"

    async def _repair(self, state: AgentState, config):
        evidence = self.deps.validator.evidence_text(
            state.get("documents") or [],
            state.get("sql_result"),
        )
        repaired = await self.deps.llm.repair(
            state["question"],
            state.get("answer", ""),
            evidence,
            state.get("validation").notes if state.get("validation") else "",
        )
        return {
            "answer": repaired,
            "validation_attempts": state.get("validation_attempts", 0) + 1,
            "trace": self._append_trace(
                state,
                "repair_node",
                "Rewrote the answer using only supported evidence before re-validation.",
            ),
        }

    async def run(self, question: str, session: AsyncSession) -> ChatResponse:
        final: AgentState = await self.graph.ainvoke(
            {
                "question": question,
                "documents": [],
                "sql_result": None,
                "trace": [],
                "validation_attempts": 0,
            },
            config={"configurable": {"session": session}},
        )
        citations = [
            Citation(
                source=doc.source,
                chunk_id=doc.chunk_id,
                excerpt=doc.content[:260],
                score=doc.score,
            )
            for doc in final.get("documents") or []
        ]
        return ChatResponse(
            answer=final.get("answer", ""),
            route=final["route_decision"].route,
            citations=citations,
            trace=final.get("trace") or [],
            sql_result=final.get("sql_result"),
            validation=final.get("validation"),
            pending_action=final.get("pending_action"),
        )

