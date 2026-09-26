ContextOps cloud deployment patch

Replace these files in your project:
- backend/Dockerfile
- render.yaml

Recommended public-demo architecture:
- Frontend: Vercel (Root Directory = frontend)
- Backend: Render Docker Web Service
- Database: Neon PostgreSQL with pgvector

Important:
1. Do NOT commit .env.
2. Hosted backend uses Gemini because your laptop Ollama is not reachable from the cloud.
3. DATABASE_URL must be the asyncpg-compatible Neon URL.
4. Enable pgvector in Neon with:
   CREATE EXTENSION IF NOT EXISTS vector;
5. Set CORS_ORIGINS on Render to your final Vercel production URL.
6. Set VITE_API_BASE_URL on Vercel to:
   https://YOUR-RENDER-SERVICE.onrender.com/api/v1
