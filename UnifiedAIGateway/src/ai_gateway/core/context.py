from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.response import ChatResponse, EmbeddingResponse
from ai_gateway.routing.base import ModelEndpoint

class GatewayContext(BaseModel):
    """Context passed through the plugin lifecycle for a single request."""
    request_id: str
    tenant_id: str
    application_id: str | None = None
    user_id: str | None = None
    
    start_time: datetime = Field(default_factory=datetime.utcnow)
    
    # Can be either chat or embeddings request
    request: ChatRequest | EmbeddingRequest | None = None
    
    # State set during routing
    selected_endpoint: ModelEndpoint | None = None
    
    # Result set after provider call
    response: ChatResponse | EmbeddingResponse | None = None
    
    # State storage for plugins to communicate
    state: dict[str, Any] = Field(default_factory=dict)
    
    # Error if one occurred
    error: Exception | None = None
    
    class Config:
        arbitrary_types_allowed = True
