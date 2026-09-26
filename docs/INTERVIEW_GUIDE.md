# Interview Guide — ContextOps

## 30-second explanation

> ContextOps is a multi-agent enterprise copilot built with LangGraph. A supervisor routes questions to document retrieval, safe SQL analytics, hybrid reasoning, or an approval-gated action path. Documents are chunked and embedded locally with all-MiniLM-L6-v2, stored in PostgreSQL with pgvector, and retrieved using cosine similarity. The answer is then validated for grounding and returned with citations and a visible tool trace. Write actions are proposed first and require human approval.

## Why LangGraph instead of a linear LangChain chain?

A linear chain works when the same steps always run. ContextOps has conditional control flow: some questions require retrieval, some SQL, some both, and write requests require approval. LangGraph makes state, branching, retries, and human-in-the-loop behavior explicit.

## What is the state?

The graph state carries the original question, route decision, retrieved chunks, SQL result, answer, validation result, trace, retry count, and any pending action.

## Why not Gemini embeddings?

Gemini is used for reasoning/generation when configured. Embeddings are generated locally with MiniLM so the retrieval layer is provider-independent, cheap to re-index, and reusable even if the LLM provider changes.

## Why pgvector?

The project already needs PostgreSQL for structured enterprise data and pending actions. pgvector keeps semantic vectors in the same operational database while still supporting cosine-distance search. At larger scale, a dedicated vector system could be considered.

## Why 384 dimensions?

`all-MiniLM-L6-v2` produces 384-dimensional sentence embeddings. The dimension is a property of the chosen model, not an arbitrary project setting.

## What is top-k retrieval?

The query is embedded and compared with stored chunk vectors. The k nearest chunks are returned as context. Too small a k may miss evidence; too large a k may add noise and consume context window.

## Why chunking?

Embedding an entire handbook into one vector destroys local detail. Chunking creates smaller semantic units. The project uses overlap so facts near a boundary are less likely to be separated from their context.

## How is hallucination reduced?

- retrieval narrows context to enterprise evidence;
- generation prompt forbids unsupported claims;
- answers include source citations;
- a validator checks grounding;
- one repair pass removes unsupported claims;
- lack of evidence results in an explicit insufficient-context response.

RAG reduces hallucination risk; it does not mathematically eliminate hallucinations.

## How is SQL made safe?

The SQL agent is read-only by design. The LLM only sees approved schemas, sqlglot parses the query, non-SELECT statements, unknown tables, and blocked PostgreSQL functions are rejected, and PostgreSQL executes the validated query in a fresh read-only transaction with a row limit.

## Agent vs workflow

A workflow has predefined steps. An agent decides which tool or path is appropriate from the current state. ContextOps combines both: the supervisor applies deterministic intent routing, while each specialist path has deterministic workflow constraints.

## Why human approval?

Read tools can safely retrieve data, but write tools affect real systems. The project demonstrates least privilege: the model may propose a typed action, but a user must explicitly approve it before the incident table is changed.

## Likely interview questions

- What exactly does the supervisor do?
- How does LangGraph represent nodes and edges?
- What happens on a hybrid query?
- Why use Sentence Transformers?
- What does cosine similarity measure?
- Why use pgvector rather than MongoDB for this project?
- How do you prevent unsafe SQL?
- What happens if the retriever returns irrelevant chunks?
- What does your validator check?
- Why only one repair attempt?
- What would you change for 10 million documents?
- How would you add authentication and tenant isolation?
- How would you evaluate retrieval quality?
- How would you add reranking?

## What to say about limitations

Be explicit:

- sample enterprise data is synthetic;
- the current retrieval pipeline is dense-only, not hybrid BM25+dense;
- no production identity provider or tenant isolation yet;
- a real system should add tracing, rate limits, a secrets manager, and offline RAG evaluation;
- Sentence Transformer startup/model memory must be sized appropriately on the deployment platform.

A candidate who knows limitations usually sounds stronger than one who calls a portfolio project "production ready."
