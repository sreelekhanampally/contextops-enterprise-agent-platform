from __future__ import annotations

from typing import Any

import sqlglot
from sqlglot import exp
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import SessionLocal
from app.schemas import SQLResult
from app.services.llm import BaseLLMService


ALLOWED_TABLES = {"departments", "tickets", "incidents"}
BLOCKED_SQL_TOKENS = {
    "pg_sleep",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "lo_import",
    "lo_export",
    "dblink",
    "set_config",
}
SCHEMA_DESCRIPTION = """
departments(id uuid, name text, owner text)
tickets(id uuid, department text, title text, status text, priority text, sla_breached boolean, created_at timestamptz)
incidents(id uuid, title text, description text, priority text, team text, status text, created_at timestamptz)
""".strip()


class UnsafeSQL(ValueError):
    pass


class SQLAgentService:
    def __init__(self, llm: BaseLLMService):
        self.llm = llm
        self.settings = get_settings()

    def validate_sql(self, sql: str) -> str:
        lowered = sql.lower()
        if any(token in lowered for token in BLOCKED_SQL_TOKENS):
            raise UnsafeSQL("Query contains a blocked PostgreSQL function")
        if ";" in sql.strip().rstrip(";"):
            raise UnsafeSQL("Multiple SQL statements are not allowed")
        parsed = sqlglot.parse_one(sql, read="postgres")
        if not isinstance(parsed, (exp.Select, exp.Union)):
            raise UnsafeSQL("Only read-only SELECT queries are allowed")
        forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Create, exp.Command, exp.Merge)
        if any(parsed.find(kind) is not None for kind in forbidden):
            raise UnsafeSQL("Write or DDL operations are forbidden")
        tables = {table.name for table in parsed.find_all(exp.Table)}
        if not tables:
            raise UnsafeSQL("Query must read from an approved analytics table")
        unknown = tables - ALLOWED_TABLES
        if unknown:
            raise UnsafeSQL(f"Query references non-approved tables: {sorted(unknown)}")
        if parsed.args.get("limit") is None:
            parsed = parsed.limit(self.settings.max_sql_rows)
        return parsed.sql(dialect="postgres")

    async def run(self, session: AsyncSession, question: str) -> SQLResult:
        draft = await self.llm.draft_sql(question, SCHEMA_DESCRIPTION)
        safe_sql = self.validate_sql(draft.sql)
        # Use a fresh session so PostgreSQL can mark the transaction read-only
        # before *any* query runs. This also keeps hybrid retrieval queries from
        # accidentally making SET TRANSACTION too late in the transaction.
        async with SessionLocal() as readonly_session:
            await readonly_session.execute(text("SET TRANSACTION READ ONLY"))
            result = await readonly_session.execute(text(safe_sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
            await readonly_session.rollback()
        return SQLResult(sql=safe_sql, columns=columns, rows=rows, explanation=draft.explanation)
