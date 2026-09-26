from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    app_name: str = "ContextOps"
    debug: bool = False
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    database_url: str = "postgresql+asyncpg://nexus:nexus@localhost:5432/nexusai"
    auto_seed: bool = True

    # mock = deterministic demo only
    # gemini = Gemini generation with optional Ollama failover
    # ollama = local generation with optional Gemini failover
    # hybrid = ordered Gemini/Ollama provider chain; control-plane logic stays deterministic
    llm_provider: Literal["gemini", "ollama", "hybrid", "mock"] = "hybrid"
    hybrid_primary: Literal["gemini", "ollama"] = "ollama"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_cooldown_seconds: int = 65
    gemini_fallback_enabled: bool = True

    ollama_enabled: bool = True
    ollama_fallback_enabled: bool = True
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout_seconds: float = 90.0
    ollama_keep_alive: str = "10m"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    top_k: int = 5
    min_similarity: float = 0.20
    embedding_batch_size: int = 64

    chunk_size: int = 800
    chunk_overlap: int = 120
    max_upload_mb: int = 10
    max_sql_rows: int = 100

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
