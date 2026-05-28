import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db_session
from app.models.document import Document
from app.schemas.document import DocumentUploadResponse, DocumentStatusResponse
from app.services.ingestion_service import run_ingestion_background
from app.services.deletion_service import soft_delete_document, hard_delete_document_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


def validate_upload_file(filename):
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail=f"file type not allowed: {ext}")
    return ext


async def save_uploaded_file(upload_file: UploadFile, document_id):
    storage_dir = Path(settings.storage_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(upload_file.filename).suffix.lower()
    dest = storage_dir / f"{document_id}{ext}"
    content = await upload_file.read()
    dest.write_bytes(content)
    return str(dest)


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename missing")

    file_ext = validate_upload_file(file.filename)
    doc_id = uuid.uuid4()
    saved_path = await save_uploaded_file(file, doc_id)

    doc = Document(
        id=doc_id,
        filename=file.filename,
        file_type=file_ext.lstrip("."),
        file_path=saved_path,
        status="PROCESSING",
    )
    db.add(doc)
    db.commit()

    background_tasks.add_task(run_ingestion_background, str(doc_id))
    logger.info("upload started %s", doc_id)
    return DocumentUploadResponse(document_id=doc_id, status="PROCESSING")


@router.get("/{document_id}", response_model=DocumentStatusResponse)
def get_document_status(document_id: uuid.UUID, db: Session = Depends(get_db_session)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    return DocumentStatusResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status,
        file_type=doc.file_type,
    )


@router.delete("/{document_id}")
def delete_document(document_id: uuid.UUID, hard: bool = False, db: Session = Depends(get_db_session)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")

    if hard:
        hard_delete_document_data(db, document_id)
        return {"document_id": str(document_id), "status": "REMOVED"}

    soft_delete_document(db, document_id)
    return {"document_id": str(document_id), "status": "DELETED"}
