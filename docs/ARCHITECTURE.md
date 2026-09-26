# ContextOps Architecture

## Design goals

1. **Route before acting.** The supervisor selects a specialist path instead of sending every prompt through one giant chain.
2. **Separate generation from retrieval.** The LLM is replaceable. Local MiniLM embeddings and pgvector form an independent retrieval layer.
3. **Keep SQL read-only.** Natural-language analytics cannot mutate operational data.
4. **Ground before returning.** A validator checks evidence support and gets one repair attempt.
5. **Never autonomously write.** Operational actions are proposals until a human approves them.

## Graph

```text
START
  ↓
supervisor
  ├── retrieval ─────────┐
  ├── sql ───────────────┤
  ├── hybrid: retrieve → sql
  ├── reasoning ─────────┤
  └── action → pending action
                         ↓
                      validator
                         ↓
               grounded? ── no → repair → validator
                  │
                 yes
                  ↓
                 END
```

## RAG path

`PDF/TXT/MD → parser → RecursiveCharacterTextSplitter → all-MiniLM-L6-v2 → pgvector`

Query time:

`query → 384-D embedding → HNSW/cosine distance → top-k chunks → similarity threshold → LLM context → citations`

## SQL path

The LLM receives a deliberately small schema. SQL is parsed with sqlglot, limited to approved tables, required to be a SELECT/UNION, checked for blocked PostgreSQL functions, and executed in a **fresh PostgreSQL read-only transaction**. A row limit is injected when absent. The fresh transaction matters on hybrid routes because document retrieval may already have used the request-scoped session.

## Hybrid path

A hybrid question uses both the retrieval and SQL paths before synthesis. Example:

> Compare the incident-response policy with our current unresolved incidents.

The retrieval agent fetches policy chunks. The SQL agent queries incidents. The reasoning node synthesizes both.

## Action path

The action planner extracts a typed `IncidentProposal`, then stores it as `pending_actions`. No incident is created yet. The UI shows Approve/Reject. Approval performs the write exactly once under a row lock.

## Validation

The validator receives the generated answer plus all evidence. If unsupported claims are detected, LangGraph routes once to `repair`, which is instructed to remove claims not supported by evidence. The second validation ends the workflow even if still imperfect, preventing loops.
