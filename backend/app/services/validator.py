from __future__ import annotations

from app.schemas import RetrievedChunk, SQLResult, ValidationResult
from app.services.llm import BaseLLMService


class GroundingValidator:
    def __init__(self, llm: BaseLLMService):
        self.llm = llm

    @staticmethod
    def evidence_text(
        documents: list[RetrievedChunk],
        sql_result: SQLResult | None,
    ) -> str:
        parts: list[str] = []
        if documents:
            doc_text = "\n\n".join(f"[{doc.source}] {doc.content}" for doc in documents)
            parts.append(f"DOCUMENTS:\n{doc_text}")
        if sql_result:
            parts.append(f"SQL:\n{sql_result.sql}\nROWS:\n{sql_result.rows}")
        return "\n\n".join(parts)

    async def validate(
        self,
        question: str,
        answer: str,
        documents: list[RetrievedChunk],
        sql_result: SQLResult | None,
    ) -> ValidationResult:
        evidence = self.evidence_text(documents, sql_result)
        return await self.llm.validate(question, answer, evidence)
