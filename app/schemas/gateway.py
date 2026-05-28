from typing import Any, Optional
from pydantic import BaseModel


class GatewayChatRequest(BaseModel):
    model: Optional[str] = None
    messages: list[dict[str, Any]]
    temperature: float = 0.2


class GatewayChatResponse(BaseModel):
    content: str
    model: str
    provider: str
