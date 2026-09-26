# Deployment

## Local Docker Compose

```bash
cp .env.example .env
# Recommended free local mode:
# LLM_PROVIDER=hybrid
# HYBRID_PRIMARY=ollama
# OLLAMA_ENABLED=true

docker compose up --build
```

For local Ollama fallback:

```bash
ollama pull qwen2.5:3b
```

Docker reaches Ollama on the host through `http://host.docker.internal:11434`.

## Recommended public demo architecture

For a simple public portfolio deployment:

- **Frontend:** Vercel (build `frontend/`)
- **Backend:** Railway or Render using `backend/Dockerfile`
- **Database:** managed PostgreSQL with the `vector` extension (Neon, Supabase, Railway Postgres, etc.)

Set `VITE_API_BASE_URL=https://YOUR-BACKEND/api/v1` on the frontend.

For the hosted backend, use Gemini directly unless you separately host an Ollama-compatible endpoint. A cloud container cannot use your laptop's `host.docker.internal` Ollama service.

Recommended hosted variables:

- `APP_ENV=production`
- `DEBUG=false`
- `DATABASE_URL=...`
- `LLM_PROVIDER=gemini`
- `GEMINI_API_KEY=...`
- `GEMINI_MODEL=gemini-3.6-flash`
- `OLLAMA_ENABLED=false`
- `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`
- `CORS_ORIGINS=https://YOUR-FRONTEND`

## Security notes for a public demo

- Never commit `.env` or provider keys.
- The repository ignores `.env` and `.env.*` except example files.
- The included database is demo data. Before using real enterprise data, add authentication/authorization around document ingestion and action approval.
- Keep `DEBUG=false` publicly so internal provider/database exceptions are not returned to clients.
- Configure platform-level rate limiting for the public API.

## Runtime sizing

The embedding model runs inside the backend container. Sentence Transformers pulls PyTorch, so the backend needs more memory and disk than a tiny serverless function. Prefer a container host with persistent or cached model storage.
