# AI Knowledge Platform

Backend RAG API — runs on your local **PostgreSQL 17** with pgvector. No Docker.

## Setup (Postgres 17)

1. Create database:

```sql
CREATE DATABASE rag;
\c rag
CREATE EXTENSION IF NOT EXISTS vector;
```

2. Python env (use **3.11–3.14**; if you are on 3.14, do not pin old `numpy` — requirements already allow `numpy>=2.4` wheels):

```powershell
cd e:\code\Actowiz
python -m venv venv
venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set `DATABASE_URL` (you already have postgres on port 5432).

4. Run API:

```powershell
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs

Tables are created automatically on first start (`init_database` in `app/core/database.py`).

## Flow

```text
Upload -> background ingestion (same process) -> chunks + embeddings in Postgres
Query  -> vector search -> LiteLLM answer
```

No Redis, no Celery, no containers.

## API examples

```powershell
curl http://localhost:8000/health

curl -X POST http://localhost:8000/documents -F "file=@data\Source_Code_Sample (2).py"

curl http://localhost:8000/documents/{document_id}

curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"query\": \"How does proxy rotation work?\", \"top_k\": 5}"
```

Wait until document `status` is `COMPLETED` before querying.

## LLM

Set `LLM_PROVIDER` and keys in `.env`. If Ollama/OpenAI is down, query still returns text from the best matching chunk.
