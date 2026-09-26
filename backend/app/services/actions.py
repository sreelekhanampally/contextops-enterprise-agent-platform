from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Incident, PendingAction
from app.schemas import ActionResolution, IncidentProposal, PendingActionView
from app.services.llm import BaseLLMService


class ActionService:
    def __init__(self, llm: BaseLLMService):
        self.llm = llm

    async def propose(self, session: AsyncSession, question: str) -> PendingActionView:
        proposal = await self.llm.propose_incident(question)
        action = PendingAction(
            action_type="create_incident",
            payload=proposal.model_dump(),
            status="pending",
        )
        session.add(action)
        await session.commit()
        await session.refresh(action)
        return PendingActionView(id=action.id, action_type="create_incident", payload=action.payload, status="pending")

    async def resolve(self, session: AsyncSession, action_id: UUID, approve: bool) -> ActionResolution:
        stmt = select(PendingAction).where(PendingAction.id == action_id).with_for_update()
        action = (await session.execute(stmt)).scalar_one_or_none()
        if action is None:
            raise ValueError("Pending action not found")
        if action.status != "pending":
            raise ValueError(f"Action has already been {action.status}")

        if not approve:
            action.status = "rejected"
            action.resolved_at = datetime.now(timezone.utc)
            await session.commit()
            return ActionResolution(action_id=action.id, status="rejected")

        if action.action_type != "create_incident":
            raise ValueError("Unsupported action type")

        proposal = IncidentProposal.model_validate(action.payload)
        incident = Incident(
            title=proposal.title,
            description=proposal.description,
            priority=proposal.priority,
            team=proposal.team,
            status="OPEN",
        )
        session.add(incident)
        await session.flush()
        action.status = "approved"
        action.resolved_at = datetime.now(timezone.utc)
        await session.commit()
        return ActionResolution(action_id=action.id, status="approved", created_incident_id=incident.id)
