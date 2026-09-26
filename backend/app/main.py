import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.config import get_settings
from app.db.init_db import init_database, seed_structured_data
from app.db.models import Document
from app.db.session import SessionLocal
from app.dependencies import get_retrieval_service
from app.routers import actions, chat, documents, health

settings = get_settings()
logger = logging.getLogger(__name__)


async def seed_documents_if_needed() -> None:
    if not settings.auto_seed:
        return
    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Document))
        if count and count > 0:
            return
        retrieval = get_retrieval_service()
        seed_dir = Path(__file__).resolve().parents[1] / "seed_documents"
        for path in sorted(seed_dir.glob("*.md")):
            await retrieval.ingest_text(
                session,
                path.name,
                "text/markdown",
                path.read_text(encoding="utf-8"),
            )


async def seed_documents_background() -> None:
    try:
        await seed_documents_if_needed()
        logger.info("Seed document ingestion completed")
    except Exception:
        logger.exception("Seed document ingestion failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()

    seed_task: asyncio.Task | None = None
    if settings.auto_seed:
        await seed_structured_data()
        # Loading Sentence Transformers can take a while on a cold cloud instance.
        # Run document embedding in the background so Render can mark the web
        # service healthy instead of timing out during application startup.
        seed_task = asyncio.create_task(seed_documents_background())

    yield

    if seed_task and not seed_task.done():
        seed_task.cancel()


app = FastAPI(
    title=f"{settings.app_name} API",
    version="1.0.0",
    description="Multi-agent enterprise RAG, analytics, and approval-gated actions.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(actions.router)
