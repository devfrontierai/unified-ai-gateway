from typing import Any, Literal
from pydantic import BaseModel, Field

# OpenAI Compatible API Request Models

class OpenAIMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None

class OpenAIChatRequest(BaseModel):
    model: str
    messages: list[OpenAIMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any | None = None
    response_format: dict[str, Any] | None = None
    user: str | None = None

class OpenAIEmbeddingRequest(BaseModel):
    model: str
    input: str | list[str]
    dimensions: int | None = None
    user: str | None = None
