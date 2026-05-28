import logging
import time
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.chunk import Chunk, Embedding
from app.models.query_log import QueryLog
from app.services.embedding_service import generate_embedding
from app.services.llm_gateway_service import generate_response
from app.schemas.query import QueryResponse, SourceItem

logger = logging.getLogger(__name__)


def search_similar_chunks(db, query_vector, top_k, filters=None):
    distance = Embedding.embedding.cosine_distance(query_vector)

    stmt = (
        select(
            Chunk,
            Document,
            distance.label("score"),
        )
        .join(Embedding, Embedding.chunk_id == Chunk.id)
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.deleted_at.is_(None))
        .where(Document.status == "COMPLETED")
    )

    if filters:
        if filters.get("file_type"):
            stmt = stmt.where(Document.file_type == filters["file_type"])
        if filters.get("document_id"):
            stmt = stmt.where(Document.id == UUID(str(filters["document_id"])))

    stmt = stmt.order_by(distance).limit(top_k)
    rows = db.execute(stmt).all()
    return rows


def build_context_from_chunks(rows):
    return [row[0].content for row in rows]


def format_query_response(answer, rows):
    sources = []
    for chunk, document, score in rows:
        sim = 1 - float(score) if score is not None else 0.0
        sources.append(SourceItem(
            document_id=document.id,
            chunk=chunk.content[:500],
            score=round(sim, 4),
        ))
    return QueryResponse(answer=answer, sources=sources)


def save_query_log(db, query_text, latency_ms, top_k):
    log_row = QueryLog(query=query_text, latency_ms=latency_ms, top_k=top_k)
    db.add(log_row)
    db.commit()


def run_rag_query(db, query_text, top_k=5, filters=None):
    started = time.time()
    filter_dict = filters.model_dump(exclude_none=True) if filters else {}

    query_vector = generate_embedding(query_text)
    rows = search_similar_chunks(db, query_vector.tolist(), top_k, filter_dict)
    context_chunks = build_context_from_chunks(rows)

    if context_chunks:
        answer = generate_response(query_text, context_chunks)
    else:
        answer = "No relevant context found in the knowledge base."

    response = format_query_response(answer, rows)
    latency_ms = (time.time() - started) * 1000
    save_query_log(db, query_text, latency_ms, top_k)
    logger.info("query done in %.2f ms", latency_ms)
    return response
