from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db_session
from app.schemas.query import QueryRequest, QueryResponse
from app.services.retrieval_service import run_rag_query

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query_knowledge(payload: QueryRequest, db: Session = Depends(get_db_session)):
    return run_rag_query(db, payload.query, payload.top_k, payload.filters)
