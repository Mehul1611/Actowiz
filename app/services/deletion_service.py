import logging
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.chunk import Chunk, Embedding
from app.services.retrieval_service import clear_query_cache

logger = logging.getLogger(__name__)


def soft_delete_document(db: Session, document_id):
    doc = db.query(Document).filter(Document.id == document_id, Document.deleted_at.is_(None)).first()
    if not doc:
        return False
    doc.deleted_at = datetime.now(timezone.utc)
    doc.status = "DELETED"
    doc.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    clear_query_cache()
    return True


def hard_delete_document_data(db: Session, document_id):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return False

    chunk_ids = [c.id for c in db.query(Chunk.id).filter(Chunk.document_id == document_id).all()]
    if chunk_ids:
        db.query(Embedding).filter(Embedding.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
        db.query(Chunk).filter(Chunk.document_id == document_id).delete(synchronize_session=False)

    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink()

    db.delete(doc)
    db.commit()

    clear_query_cache()

    logger.info("hard deleted document %s", document_id)
    return True
