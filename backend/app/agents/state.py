from __future__ import annotations

from typing import TypedDict

from app.schemas import PendingActionView, RetrievedChunk, RouteDecision, SQLResult, TraceEvent, ValidationResult


class AgentState(TypedDict, total=False):
    question: str
    route_decision: RouteDecision
    documents: list[RetrievedChunk]
    sql_result: SQLResult | None
    answer: str
    validation: ValidationResult | None
    validation_attempts: int
    trace: list[TraceEvent]
    pending_action: PendingActionView | None
