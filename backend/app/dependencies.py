from functools import lru_cache

from app.agents.graph import ContextOpsAgentGraph, GraphDependencies
from app.services.actions import ActionService
from app.services.embeddings import LocalEmbeddingService
from app.services.llm import build_llm_service
from app.services.retrieval import RetrievalService
from app.services.sql_agent import SQLAgentService
from app.services.validator import GroundingValidator


@lru_cache
def get_embedding_service() -> LocalEmbeddingService:
    return LocalEmbeddingService()


@lru_cache
def get_llm_service():
    return build_llm_service()


@lru_cache
def get_retrieval_service() -> RetrievalService:
    return RetrievalService(get_embedding_service())


@lru_cache
def get_action_service() -> ActionService:
    return ActionService(get_llm_service())


@lru_cache
def get_sql_agent_service() -> SQLAgentService:
    return SQLAgentService(get_llm_service())


@lru_cache
def get_validator_service() -> GroundingValidator:
    return GroundingValidator(get_llm_service())


@lru_cache
def get_agent_graph() -> ContextOpsAgentGraph:
    deps = GraphDependencies(
        llm=get_llm_service(),
        retrieval=get_retrieval_service(),
        sql_agent=get_sql_agent_service(),
        actions=get_action_service(),
        validator=get_validator_service(),
    )
    return ContextOpsAgentGraph(deps)
