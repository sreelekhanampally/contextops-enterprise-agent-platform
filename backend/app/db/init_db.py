from pathlib import Path

from sqlalchemy import func, select, text

from app.config import get_settings
from app.db.models import Base, Department, Incident, Ticket
from app.db.session import SessionLocal, engine

settings = get_settings()


async def init_database() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)


async def seed_structured_data() -> None:
    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Department))
        if count and count > 0:
            return

        session.add_all([
            Department(name="Platform Engineering", owner="Asha Rao"),
            Department(name="Customer Support", owner="Rahul Mehta"),
            Department(name="Security", owner="Neha Iyer"),
            Department(name="Finance", owner="Arjun Shah"),
        ])

        session.add_all([
            Ticket(department="Platform Engineering", title="Database connection pool saturation", status="OPEN", priority="HIGH", sla_breached=True),
            Ticket(department="Platform Engineering", title="Kubernetes node disk pressure", status="OPEN", priority="MEDIUM", sla_breached=False),
            Ticket(department="Platform Engineering", title="API latency regression", status="OPEN", priority="HIGH", sla_breached=True),
            Ticket(department="Customer Support", title="Refund queue backlog", status="OPEN", priority="MEDIUM", sla_breached=False),
            Ticket(department="Customer Support", title="Login help article outdated", status="CLOSED", priority="LOW", sla_breached=False),
            Ticket(department="Security", title="Rotate exposed sandbox credential", status="OPEN", priority="CRITICAL", sla_breached=True),
            Ticket(department="Finance", title="Monthly export mismatch", status="CLOSED", priority="MEDIUM", sla_breached=False),
        ])

        session.add_all([
            Incident(title="Checkout API latency", description="Elevated P95 latency in checkout API.", priority="HIGH", team="Platform Engineering", status="OPEN"),
            Incident(title="Sandbox credential exposure", description="Credential discovered in internal test logs.", priority="CRITICAL", team="Security", status="INVESTIGATING"),
        ])
        await session.commit()
