from __future__ import annotations

import asyncio
import math
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

from app.config import get_settings


class LocalEmbeddingService:
    """Embedding service with local MiniLM and Gemini cloud backends.

    Local development keeps the original Sentence Transformer implementation.
    Hosted environments can use Gemini embeddings to avoid loading PyTorch and
    the transformer model into a memory-constrained web process.
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

    @staticmethod
    def _normalize(values: list[float]) -> list[float]:
        magnitude = math.sqrt(sum(value * value for value in values))
        if magnitude <= 0:
            return values
        return [value / magnitude for value in values]

    @property
    def _gemini_model_resource(self) -> str:
        model = self.model_name.removeprefix("models/")
        return f"models/{model}"

    async def _embed_gemini_single(self, text: str, task_type: str) -> list[float]:
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for Gemini embeddings")

        model_resource = self._gemini_model_resource
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"{model_resource}:embedContent"
        )
        payload = {
            "model": model_resource,
            "content": {"parts": [{"text": text}]},
            "embedContentConfig": {
                "taskType": task_type,
                "outputDimensionality": self.settings.embedding_dim,
            },
        }
        headers = {
            "x-goog-api-key": self.settings.gemini_api_key,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.settings.embedding_timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            values = response.json()["embedding"]["values"]
        return self._normalize([float(value) for value in values])

    async def _embed_gemini_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for Gemini embeddings")

        model_resource = self._gemini_model_resource
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"{model_resource}:batchEmbedContents"
        )
        headers = {
            "x-goog-api-key": self.settings.gemini_api_key,
            "Content-Type": "application/json",
        }

        # Keep requests modest so seed ingestion and uploads remain reliable
        # on free-tier API quotas and small cloud instances.
        batch_size = max(1, min(self.settings.embedding_batch_size, 32))
        vectors: list[list[float]] = []

        async with httpx.AsyncClient(timeout=self.settings.embedding_timeout_seconds) as client:
            for start in range(0, len(texts), batch_size):
                batch = texts[start : start + batch_size]
                payload = {
                    "requests": [
                        {
                            "model": model_resource,
                            "content": {"parts": [{"text": text}]},
                            "embedContentConfig": {
                                "taskType": "RETRIEVAL_DOCUMENT",
                                "outputDimensionality": self.settings.embedding_dim,
                            },
                        }
                        for text in batch
                    ]
                }
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                for item in response.json()["embeddings"]:
                    values = [float(value) for value in item["values"]]
                    vectors.append(self._normalize(values))

        return vectors

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.settings.embedding_provider == "gemini":
            return await self._embed_gemini_documents(texts)

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
        if self.settings.embedding_provider == "gemini":
            return await self._embed_gemini_single(text, "RETRIEVAL_QUERY")
        return (await self.embed_documents([text]))[0]
