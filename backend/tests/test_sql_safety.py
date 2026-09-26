import pytest

from app.services.llm import MockLLMService
from app.services.sql_agent import SQLAgentService, UnsafeSQL


def test_allows_select_and_adds_limit():
    service = SQLAgentService(MockLLMService())
    sql = service.validate_sql("SELECT department, COUNT(*) FROM tickets GROUP BY department")
    assert "LIMIT" in sql.upper()
    assert "tickets" in sql


@pytest.mark.parametrize("sql", [
    "DELETE FROM tickets",
    "UPDATE tickets SET status='CLOSED'",
    "DROP TABLE tickets",
    "SELECT * FROM secrets",
    "SELECT * FROM tickets; DELETE FROM tickets",
    "SELECT pg_sleep(10) FROM tickets LIMIT 1",
    "SELECT 1",
])
def test_rejects_unsafe_sql(sql):
    service = SQLAgentService(MockLLMService())
    with pytest.raises(UnsafeSQL):
        service.validate_sql(sql)
