import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.document import Document
from app.models.chunk import Chunk, Embedding
from app.utils.file_loader import load_file_content
from app.services.chunking_service import chunk_text
from app.services.embedding_service import generate_embeddings_batch

logger = logging.getLogger(__name__)


def mark_document_status(db, document_id, status):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return None
    doc.status = status
    doc.updated_at = datetime.now(timezone.utc)
    db.commit()
    return doc


def store_chunks_and_embeddings(db, document_id, chunk_items, vectors):
    for item, vector in zip(chunk_items, vectors):
        chunk_row = Chunk(
            document_id=document_id,
            chunk_index=item["index"],
            content=item["content"],
            chunk_metadata=item.get("metadata", {}),
        )
        db.add(chunk_row)
        db.flush()

        emb = Embedding(chunk_id=chunk_row.id, embedding=vector.tolist())
        db.add(emb)
    db.commit()


def process_document_content(db: Session, document: Document):
    logger.info("processing document %s", document.id)
    text = load_file_content(document.file_path, document.file_type)
    if not text:
        logger.warning("document %s failed: no text extracted", document.id)
        mark_document_status(db, document.id, "FAILED")
        return

    chunk_items = chunk_text(text, document.file_type)
    if not chunk_items:
        logger.warning("document %s failed: chunking produced nothing", document.id)
        mark_document_status(db, document.id, "FAILED")
        return

    texts = [c["content"] for c in chunk_items]
    vectors = generate_embeddings_batch(texts)
    store_chunks_and_embeddings(db, document.id, chunk_items, vectors)
    mark_document_status(db, document.id, "COMPLETED")
    logger.info("document %s completed with %s chunks", document.id, len(chunk_items))


def run_ingestion_background(document_id):
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == UUID(str(document_id))).first()
        if not doc or doc.deleted_at is not None:
            return
        mark_document_status(db, doc.id, "PROCESSING")
        process_document_content(db, doc)
    except Exception:
        logger.exception("ingestion failed for %s", document_id)
        mark_document_status(db, UUID(str(document_id)), "FAILED")
    finally:
        db.close()
