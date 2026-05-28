from fastapi import APIRouter, HTTPException
from app.schemas.gateway import GatewayChatRequest, GatewayChatResponse
from app.services.llm_gateway_service import send_gateway_chat

router = APIRouter(prefix="/gateway", tags=["gateway"])


@router.post("/chat", response_model=GatewayChatResponse)
def gateway_chat(payload: GatewayChatRequest):
    try:
        result = send_gateway_chat(payload.messages, payload.model, payload.temperature)
        return GatewayChatResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
