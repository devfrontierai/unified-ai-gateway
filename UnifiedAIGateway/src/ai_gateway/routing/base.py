from abc import ABC, abstractmethod
from pydantic import BaseModel
from ai_gateway.core.request import ChatRequest

class ModelEndpoint(BaseModel):
    provider_name: str
    provider: Any
    provider_model: str
    class Config:
        arbitrary_types_allowed = True

class RoutingStrategy(ABC):
    @abstractmethod
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        ...
