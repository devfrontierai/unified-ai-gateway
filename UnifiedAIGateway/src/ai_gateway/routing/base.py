from abc import ABC, abstractmethod
from pydantic import BaseModel

from ai_gateway.core.request import ChatRequest
from ai_gateway.providers.base import ModelProvider

class ModelEndpoint(BaseModel):
    provider_name: str
    provider: ModelProvider
    provider_model: str
    
    class Config:
        arbitrary_types_allowed = True

class RoutingStrategy(ABC):
    """Base strategy for routing a request across multiple provider endpoints."""

    @abstractmethod
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        ...
