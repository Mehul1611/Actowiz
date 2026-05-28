from uuid import UUID
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    status: str


class DocumentStatusResponse(BaseModel):
    document_id: UUID
    filename: str
    status: str
    file_type: str
