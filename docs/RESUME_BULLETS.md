# Resume bullets — use only after you have run and verified the project

**ContextOps — Enterprise Knowledge & Action Platform**

- Built a **LangGraph-orchestrated enterprise AI copilot** that routes natural-language requests across RAG retrieval, read-only SQL analytics, hybrid reasoning, and approval-gated action workflows.
- Implemented a **local Sentence Transformer + pgvector RAG pipeline** for PDF/TXT/Markdown knowledge, with top-k cosine retrieval, source citations, and grounded LLM synthesis through Gemini.
- Added **SQL AST validation, grounding verification with repair, execution traces, and human-in-the-loop incident creation**, separating read tools from privileged write actions.

**Tech:** Python, FastAPI, LangGraph, LangChain, Gemini, Sentence Transformers, PostgreSQL, pgvector, React, TypeScript, Docker


### Free-tier / reliability bullet
- Reduced cloud-LLM usage with a deterministic control plane for routing, validation, SQL safety, and action extraction, plus Gemini-to-Ollama failover with quota-aware circuit breaking for resilient local inference.
