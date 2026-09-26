from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

from app.config import get_settings


class LocalEmbeddingService:
    """Lazy local Sentence Transformer embeddings.

    The model is intentionally independent from the LLM provider so retrieval can be
    swapped or run without paying a provider for every document embedding.
    """

    def __init__(self, model_name: str | None = None):
        self.settings = get_settings()
        self.model_name = model_name or self.settings.embedding_model
        self._model: Any | None = None
        self._lock = asyncio.Lock()

    async def _ensure_model(self) -> "SentenceTransformer":
        if self._model is not None:
            return self._model
        async with self._lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer

                self._model = await asyncio.to_thread(SentenceTransformer, self.model_name)
        return self._model

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = await self._ensure_model()
        vectors = await asyncio.to_thread(
            model.encode,
            texts,
            batch_size=self.settings.embedding_batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed_documents([text]))[0]
