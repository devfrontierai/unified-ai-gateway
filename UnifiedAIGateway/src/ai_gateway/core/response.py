from typing import Any, AsyncIterator
from pydantic import BaseModel

class ChatChoice(BaseModel):
    index: int
    message: dict[str, Any]
    finish_reason: str | None = None

class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatResponse(BaseModel):
    """Canonical internal response model for chat completions."""
    id: str
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage | None = None
    created: int
    
    metadata: dict[str, Any] = {}

class ChatChunkChoice(BaseModel):
    index: int
    delta: dict[str, Any]
    finish_reason: str | None = None

class ChatChunk(BaseModel):
    """Canonical internal response model for streaming chat chunks."""
    id: str
    model: str
    choices: list[ChatChunkChoice]
    created: int
    usage: ChatUsage | None = None

class EmbeddingData(BaseModel):
    object: str = "embedding"
    index: int
    embedding: list[float]

class EmbeddingResponse(BaseModel):
    """Canonical internal response model for embeddings."""
    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: ChatUsage | None = None
