from typing import Any, Literal
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None

class ToolDefinition(BaseModel):
    type: Literal["function"]
    function: dict[str, Any]

class ChatRequest(BaseModel):
    """Canonical internal request model for chat completions."""
    request_id: str
    tenant_id: str
    application_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None

    model: str
    messages: list[Message]

    temperature: float | None = None
    max_tokens: int | None = None

    tools: list[ToolDefinition] | None = None
    tool_choice: Any | None = None

    stream: bool = False
    response_format: dict[str, Any] | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

class EmbeddingRequest(BaseModel):
    """Canonical internal request model for embeddings."""
    request_id: str
    tenant_id: str
    application_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None

    model: str
    input: str | list[str]
    dimensions: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
