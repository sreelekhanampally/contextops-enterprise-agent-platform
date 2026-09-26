from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_action_service
from app.schemas import ActionResolution
from app.services.actions import ActionService

router = APIRouter(prefix="/api/v1/actions", tags=["actions"])


@router.post("/{action_id}/approve", response_model=ActionResolution)
async def approve_action(
    action_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: ActionService = Depends(get_action_service),
):
    try:
        return await service.resolve(session, action_id, True)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{action_id}/reject", response_model=ActionResolution)
async def reject_action(
    action_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: ActionService = Depends(get_action_service),
):
    try:
        return await service.resolve(session, action_id, False)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
