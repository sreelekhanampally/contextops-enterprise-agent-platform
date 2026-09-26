from __future__ import annotations

import io
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Document, KnowledgeChunk
from app.schemas import RetrievedChunk
from app.services.embeddings import LocalEmbeddingService


class RetrievalService:
    def __init__(self, embeddings: LocalEmbeddingService):
        self.settings = get_settings()
        self.embeddings = embeddings
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    async def retrieve(
        self,
        session: AsyncSession,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        vector = await self.embeddings.embed_query(query)
        distance = KnowledgeChunk.embedding.cosine_distance(vector).label("distance")
        stmt = (
            select(KnowledgeChunk, distance)
            .order_by(distance)
            .limit(top_k or self.settings.top_k)
        )
        rows = (await session.execute(stmt)).all()
        retrieved: list[RetrievedChunk] = []
        for chunk, dist in rows:
            score = max(0.0, 1.0 - float(dist))
            if score < self.settings.min_similarity:
                continue
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(chunk.id),
                    source=chunk.source,
                    content=chunk.content,
                    score=score,
                )
            )
        return retrieved

    async def ingest_upload(self, session: AsyncSession, file: UploadFile) -> tuple[UUID, int]:
        raw = await file.read()
        if len(raw) > self.settings.max_upload_mb * 1024 * 1024:
            raise ValueError(f"File exceeds {self.settings.max_upload_mb} MB limit")

        suffix = Path(file.filename or "upload.txt").suffix.lower()
        if suffix not in {".pdf", ".txt", ".md"}:
            raise ValueError("Only PDF, TXT, and Markdown files are supported")

        text = self._parse_bytes(raw, suffix)
        return await self.ingest_text(
            session,
            file.filename or "upload",
            file.content_type or "text/plain",
            text,
        )

    async def ingest_text(
        self,
        session: AsyncSession,
        source: str,
        mime_type: str,
        text: str,
    ) -> tuple[UUID, int]:
        chunks = [chunk.strip() for chunk in self.splitter.split_text(text) if chunk.strip()]
        if not chunks:
            raise ValueError("Document contains no extractable text")

        vectors = await self.embeddings.embed_documents(chunks)
        doc = Document(filename=source, mime_type=mime_type)
        session.add(doc)
        await session.flush()

        session.add_all(
            [
                KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=index,
                    source=source,
                    content=chunk,
                    embedding=vector,
                )
                for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
            ]
        )
        await session.commit()
        return doc.id, len(chunks)

    @staticmethod
    def _parse_bytes(raw: bytes, suffix: str) -> str:
        if suffix == ".pdf":
            reader = PdfReader(io.BytesIO(raw))
            return "\n\n".join((page.extract_text() or "") for page in reader.pages)
        return raw.decode("utf-8", errors="replace")
