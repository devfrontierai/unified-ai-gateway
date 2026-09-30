from abc import ABC, abstractmethod
from typing import AsyncIterator, Any
from pydantic import BaseModel

from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.response import ChatResponse, ChatChunk, EmbeddingResponse
from ai_gateway.core.capabilities import ModelCapabilities

class ModelInfo(BaseModel):
    id: str
    capabilities: ModelCapabilities

class ProviderHealth(BaseModel):
    status: str
    details: dict[str, Any] = {}

class ModelProvider(ABC):
    """Base interface for all model providers."""

    @abstractmethod
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        ...

    @abstractmethod
    async def stream_chat_completion(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        ...

    @abstractmethod
    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        ...

    @abstractmethod
    async def health(self) -> ProviderHealth:
        ...
