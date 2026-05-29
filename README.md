# AI Knowledge Platform

## Project Overview

The AI Knowledge Platform is an **internal AI knowledge platform** that turns your
documents into a searchable, question-answering knowledge base.

It implements a full **RAG (Retrieval-Augmented Generation) pipeline**: documents are
uploaded, parsed, split into chunks, embedded into vectors, and stored in PostgreSQL
with `pgvector`. When you ask a question, the platform runs **semantic search** over
those vectors to find the most relevant chunks, then passes them to an LLM (through a
gateway) to generate a grounded answer with source references.

In short:

- Ingest PDFs, markdown, and code files.
- Index them as embeddings for semantic search.
- Ask natural-language questions and get answers backed by your own documents.

## Features

- Upload PDF, markdown, and code files (`.pdf`, `.md`, `.txt`, `.py`, `.js`, `.java`)
- Scanned-PDF OCR fallback (RapidOCR) when a page has no selectable text
- Semantic search using pgvector
- AI Gateway integration (LiteLLM: Ollama / OpenAI / Anthropic)
- Async ingestion pipeline (uploads return immediately, processing runs in background)
- Symbol-aware chunking for code, token-window chunking for text
- Soft delete + hard delete
- Metadata filtering (by `file_type` or `document_id`)
- HNSW vector indexing with cosine similarity
- Query caching (LRU) and per-query latency logging
- JSON structured logging and a health endpoint

## Tech Stack

| Layer            | Technology                                          |
| ---------------- | --------------------------------------------------- |
| Backend          | FastAPI                                             |
| Database         | PostgreSQL + pgvector                               |
| Embeddings       | sentence-transformers (`all-MiniLM-L6-v2`, 384-dim) |
| LLM Gateway      | LiteLLM                                             |
| Vector Search    | Cosine similarity (HNSW index)                      |
| PDF / OCR        | PyMuPDF + RapidOCR                                  |
| ORM / Validation | SQLAlchemy 2.0 + Pydantic                           |

## Architecture Diagram

System flow (exported from draw.io):

![Architecture diagram](docs/architecture.png)

Database schema:

![Database schema](docs/database-schema.png)

```text
Upload  ->  async ingestion  ->  text extraction  ->  chunking  ->  embeddings  ->  Postgres (pgvector)
Query   ->  embed query  ->  cosine vector search  ->  LLM answer (LiteLLM)  ->  response with sources
```

## API Endpoints

| Method   | Endpoint            | Description                                          |
| -------- | ------------------- | ---------------------------------------------------- |
| `GET`    | `/health`           | Service and PostgreSQL connectivity check            |
| `POST`   | `/documents`        | Upload a document; ingestion runs asynchronously     |
| `GET`    | `/documents/{id}`   | Get a document's processing status                   |
| `DELETE` | `/documents/{id}`   | Soft delete (use `?hard=true` to remove data + file) |
| `POST`   | `/query`            | Ask a question over the ingested documents           |
| `POST`   | `/gateway/chat`     | Direct LLM chat passthrough via LiteLLM              |

## How to Run

### 1. Database setup

PostgreSQL 17 with the `vector` extension available. Create the database and enable
`pgvector`:

```sql
CREATE DATABASE rag;
\c rag
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Install dependencies

Python 3.11–3.14.

```powershell
cd e:\code\Actowiz
python -m venv venv
venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and set at least `DATABASE_URL`:

```powershell
copy .env.example .env
```

Key variables:

| Variable          | Description                        | Default                                  |
| ----------------- | ---------------------------------- | ---------------------------------------- |
| `DATABASE_URL`    | PostgreSQL connection string       | `postgresql://postgres:postgres@localhost:5432/rag` |
| `EMBEDDING_MODEL` | Sentence-Transformers model name   | `sentence-transformers/all-MiniLM-L6-v2` |
| `LLM_PROVIDER`    | `ollama`, `openai`, or `anthropic` | `ollama`                                 |
| `LLM_MODEL`       | Model name for the provider        | `llama3.2`                               |
| `OLLAMA_BASE_URL` | Ollama server URL                  | `http://localhost:11434`                 |

### 4. Run the API

```powershell
uvicorn app.main:app --reload
```

Tables, the `vector` extension, and the HNSW index are created automatically on first
start (see `init_database` in `app/core/database.py`).

Open the interactive docs at http://localhost:8000/docs

## Example Queries

```powershell
# Health check
curl http://localhost:8000/health

# Upload a document
curl -X POST http://localhost:8000/documents -F "file=@data\Source_Code_Sample (2).py"

# Check ingestion status (wait until status is COMPLETED before querying)
curl http://localhost:8000/documents/{document_id}

# Ask a question
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"query\": \"How does proxy rotation work?\", \"top_k\": 5}"

# Query with metadata filtering
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"query\": \"How does proxy rotation work?\", \"top_k\": 5, \"filters\": {\"file_type\": \"py\"}}"

# Hard delete a document (removes chunks, embeddings, and the stored file)
curl -X DELETE "http://localhost:8000/documents/{document_id}?hard=true"
```

Example query response:

```json
{
  "answer": "Proxy rotation cycles through a pool of proxies on each request ...",
  "sources": [
    {
      "document_id": "f1c2...",
      "chunk": "def rotate_proxy(self): ...",
      "score": 0.83
    }
  ]
}
```

## Project Structure

```text
app/
  api/routes/      FastAPI routers (health, documents, query, gateway)
  core/            config, database, logging, declarative base
  models/          SQLAlchemy models (Document, Chunk, Embedding, QueryLog)
  schemas/         Pydantic request/response models
  services/        ingestion, chunking, embedding, retrieval, gateway, deletion
  utils/           file loading, PDF/OCR parsing, tokenization
  prompts/         RAG prompt template
  main.py          app entrypoint
docs/              architecture and database-schema diagrams
```
