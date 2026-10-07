import random
from ai_gateway.core.request import ChatRequest
from ai_gateway.routing.base import RoutingStrategy, ModelEndpoint

class StaticStrategy(RoutingStrategy):
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates: raise ValueError("No candidates")
        return candidates[0]

class RoundRobinStrategy(RoutingStrategy):
    def __init__(self):
        self._index = 0
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates: raise ValueError("No candidates")
        selected = candidates[self._index % len(candidates)]
        self._index += 1
        return selected

class WeightedStrategy(RoutingStrategy):
    def __init__(self, weights: list[float]):
        self.weights = weights
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates: raise ValueError("No candidates")
        if len(self.weights) != len(candidates): return candidates[0]
        return random.choices(candidates, weights=self.weights, k=1)[0]

class FallbackStrategy(RoutingStrategy):
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates: raise ValueError("No candidates")
        return candidates[0]
