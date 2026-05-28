from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class QueryFilters(BaseModel):
    file_type: Optional[str] = None
    document_id: Optional[UUID] = None


class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Optional[QueryFilters] = None


class SourceItem(BaseModel):
    document_id: UUID
    chunk: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
