from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


RouteName = Literal["retrieval", "sql", "hybrid", "reasoning", "action"]


class RouteDecision(BaseModel):
    route: RouteName
    rationale: str = Field(min_length=1, max_length=500)


class Citation(BaseModel):
    source: str
    chunk_id: str
    excerpt: str
    score: float | None = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    source: str
    content: str
    score: float


class SQLResult(BaseModel):
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    explanation: str = ""


class TraceEvent(BaseModel):
    node: str
    detail: str


class ValidationResult(BaseModel):
    grounded: bool
    confidence: float = Field(ge=0, le=1)
    notes: str
    unsupported_claims: list[str] = Field(default_factory=list)


class PendingActionView(BaseModel):
    id: UUID
    action_type: Literal["create_incident"]
    payload: dict[str, Any]
    status: Literal["pending", "approved", "rejected"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    route: RouteName
    citations: list[Citation] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    sql_result: SQLResult | None = None
    validation: ValidationResult | None = None
    pending_action: PendingActionView | None = None


class IncidentProposal(BaseModel):
    title: str = Field(min_length=4, max_length=200)
    description: str = Field(min_length=4, max_length=2000)
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"
    team: str = Field(min_length=2, max_length=120)


class SQLDraft(BaseModel):
    sql: str
    explanation: str


class DocumentIngestResponse(BaseModel):
    document_id: UUID
    filename: str
    chunks_created: int


class ActionResolution(BaseModel):
    action_id: UUID
    status: Literal["approved", "rejected"]
    created_incident_id: UUID | None = None


class HealthResponse(BaseModel):
    status: str
    app: str
    llm_provider: str
    embedding_model: str
    database: str
