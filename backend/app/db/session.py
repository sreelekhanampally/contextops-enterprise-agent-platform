from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

database_url = settings.database_url.strip()

# Neon and many hosting dashboards provide a standard PostgreSQL URL.
# This service uses SQLAlchemy's async engine with asyncpg, so normalize
# common Postgres URL schemes before creating the engine.
if database_url.startswith("postgresql+psycopg://"):
    database_url = database_url.replace(
        "postgresql+psycopg://",
        "postgresql+asyncpg://",
        1,
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1,
    )

# Neon connection strings commonly use libpq-style query parameters.
# asyncpg expects "ssl=require" and does not need channel_binding here.
database_url = database_url.replace("sslmode=require", "ssl=require")
database_url = database_url.replace("&channel_binding=require", "")
database_url = database_url.replace("channel_binding=require&", "")

engine = create_async_engine(database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
