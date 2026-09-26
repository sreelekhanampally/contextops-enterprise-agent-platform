import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import ContextOpsAgentGraph
from app.config import get_settings
from app.db.session import get_db
from app.dependencies import get_agent_graph
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db),
    graph: ContextOpsAgentGraph = Depends(get_agent_graph),
):
    try:
        return await graph.run(payload.message, session)
    except Exception as exc:
        logger.exception("ContextOps workflow failed")
        detail = f"Agent workflow failed: {exc}" if settings.debug else "Agent workflow failed. Please retry."
        raise HTTPException(status_code=500, detail=detail) from exc
