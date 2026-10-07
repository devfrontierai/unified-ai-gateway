from datetime import datetime
from pydantic import BaseModel, Field

class BaseEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str
    tenant_id: str
    application_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None

class ModelCallEvent(BaseEvent):
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float
    status: str
    estimated_cost: float | None = None
    error_message: str | None = None
