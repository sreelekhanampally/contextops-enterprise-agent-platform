# ContextOps — Enterprise Knowledge & Action Platform

ContextOps is an **agentic enterprise knowledge and action platform** for grounded retrieval, structured analytics, and approval-gated actions. A LangGraph workflow routes each request to the appropriate specialist path, retrieves evidence from PostgreSQL + pgvector, queries structured business data safely, validates groundedness, and requires human approval before any write action.

## Why this project exists

Employees need answers that may live in very different places:

- HR policies and FAQs
- engineering documentation
- product manuals
- incident-response runbooks
- structured operational tables such as tickets and incidents

A single retrieval chain is not enough. ContextOps routes each question to the right capability and returns a trace showing what happened.


## Free-tier resilient inference

ContextOps deliberately avoids spending an LLM request on every graph node. Routing, action extraction, SQL safety, and grounding checks are deterministic. Common SQL intents are also templated. Gemini or Ollama is reserved for language generation and unfamiliar SQL drafting.

When `LLM_PROVIDER=hybrid`, ContextOps can use Gemini and automatically fail over to a local Ollama model. A Gemini 429/quota error opens a short circuit breaker, so subsequent requests skip Gemini during the cooldown instead of repeatedly waiting for the same rate limit.

Recommended local fallback:

```bash
ollama pull qwen2.5:3b
```

Docker reaches the host Ollama service through `http://host.docker.internal:11434`.

With the common demo queries, retrieval, SQL, and hybrid paths normally require only **one generative model call** for the final answer; action proposals use **zero** model calls until a human explicitly approves the write.

## Architecture

```text
                         User
                          │
                          ▼
                 LangGraph Supervisor
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
   Retrieval Agent     SQL Agent     Reasoning Agent
          │               │                │
          ▼               ▼                ▼
      pgvector        PostgreSQL           LLM
          │               │                │
          └───────────────┬────────────────┘
                          ▼
                   Validator Agent
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
     Grounded Answer            Repair / Refuse
      + Citations

Action requests follow a separate safety path:

User → Supervisor → Action Planner → Pending Action → Human Approve/Reject → Database write
```

## Core features

- **LangGraph orchestration** with conditional routing
- **Supervisor/router** for retrieval, SQL, hybrid, reasoning, or action intent
- **RAG retrieval** over local `all-MiniLM-L6-v2` 384-dimensional embeddings
- **PostgreSQL + pgvector** cosine-similarity search with an HNSW vector index
- **Document ingestion** for PDF, TXT, and Markdown
- **Safe SQL agent** with SQL AST validation and read-only execution
- **Hybrid queries** that combine document evidence with structured analytics
- **Grounding validator** with one repair pass before returning unsupported content
- **Citations** for retrieved evidence
- **Human-in-the-loop actions** for incident creation
- **Execution trace** visible in the UI
- **FastAPI backend + React frontend + Docker Compose**
- **Gemini/Ollama generation with deterministic routing** and a deterministic mock mode for tests

## Tech stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| LLM integration | LangChain |
| LLM | Gemini 3.6 Flash + optional local Ollama fallback |
| Embeddings | Sentence Transformers `all-MiniLM-L6-v2` |
| Vector database | PostgreSQL + pgvector |
| Backend | FastAPI + SQLAlchemy async |
| Frontend | React + TypeScript + Vite |
| Validation | Pydantic + grounding checks |
| Containers | Docker Compose |

## Quick start with Docker

1. Copy environment values:

```bash
cp .env.example .env
```

2. Add a Gemini key to `.env` for real LLM generation, or set `LLM_PROVIDER=mock` for deterministic local development.

3. Start the stack:

```bash
docker compose up --build
```

4. Open:

- App: http://localhost:8080
- FastAPI docs: http://localhost:8000/docs

The database is seeded automatically with sample enterprise policies, departments, tickets, and incidents.

## Example questions

- `How many annual leave days do employees receive?`
- `Which department has the highest number of open tickets?`
- `Compare the incident response policy with the current unresolved incidents.`
- `What should an engineer do after discovering a production security incident?`
- `Create a high-priority incident for a production database outage assigned to Platform Engineering.`

The last prompt **does not write immediately**. ContextOps creates a pending action and waits for explicit approval in the UI.

## Document ingestion

The UI supports PDF/TXT/Markdown uploads. The backend:

```text
file → parse → recursive chunking → MiniLM embeddings → pgvector
```

Embeddings are generated locally rather than through Gemini. This keeps the retrieval layer provider-independent and avoids per-document embedding API costs.

## Safe SQL design

The SQL agent is constrained in four layers:

1. the LLM is shown only the approved analytics schema;
2. generated SQL is parsed with `sqlglot` and must be a single read-only SELECT;
3. blocked PostgreSQL functions and non-approved tables are rejected;
4. execution happens in a fresh PostgreSQL read-only transaction and is capped with a hard row limit.

Write operations never go through the SQL agent.

## Human-in-the-loop actions

The action planner can propose incident creation, but it only creates a `pending_actions` row. A separate approval endpoint performs the final write after a user clicks **Approve**.

This gives a clean interview example of the difference between:

- read tools,
- write tools,
- agent planning,
- authorization,
- and human approval.

## Repository layout

```text
backend/
  app/
    agents/       LangGraph state + graph nodes
    db/           SQLAlchemy models/session/seed
    routers/      FastAPI routes
    services/     LLM, embeddings, retrieval, SQL, actions, validation
  seed_documents/ sample enterprise corpus
  tests/          unit tests
frontend/
  src/             React application
  nginx.conf       production API proxy

docs/
  ARCHITECTURE.md
  INTERVIEW_GUIDE.md
  DEPLOYMENT.md
```

## Evaluation

The repository includes backend unit tests for:

- routing decisions
- SQL safety
- grounding behavior
- action approval rules
- graph-level behavior using deterministic fakes

Run:

```bash
cd backend
pytest -q
```

It also contains a small reproducible evaluation set for **routing accuracy** and
**retrieval Hit@K**:

```bash
cd backend
python -m eval.run_eval
```

The evaluation intentionally reports interpretable metrics rather than inventing
an opaque "AI accuracy" number. Add more cases as the knowledge base grows.

## Architecture in one paragraph

A concise version:

> ContextOps is a multi-agent enterprise copilot orchestrated with LangGraph. A deterministic supervisor classifies each request and routes it to document retrieval, structured SQL analytics, hybrid reasoning, or an approval-gated action flow. Documents are chunked and embedded locally with all-MiniLM-L6-v2, stored in pgvector, and retrieved with cosine similarity. The final answer is grounded in retrieved evidence or SQL results, passed through a validation node, and returned with citations and an execution trace. Write actions are never executed autonomously; they require explicit human approval.

See `docs/INTERVIEW_GUIDE.md` for a deeper walkthrough.
