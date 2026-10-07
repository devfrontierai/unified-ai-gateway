from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field
from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.response import ChatResponse, EmbeddingResponse

class GatewayContext(BaseModel):
    request_id: str
    tenant_id: str
    application_id: str | None = None
    user_id: str | None = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    request: ChatRequest | EmbeddingRequest | None = None
    selected_endpoint: Any | None = None
    response: ChatResponse | EmbeddingResponse | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    error: Exception | None = None
    
    class Config:
        arbitrary_types_allowed = True
